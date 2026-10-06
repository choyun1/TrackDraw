// The page shell: tabs, duration, synthesis engine, playback, the result,
// undo, reset, save, open, links and the log (docs/design/app.md, "One tab, one route back
// to sound"). Tabs plug in through a small contract: a document to edit, a
// `commit` callback when an edit ends, and a picture of the last result.

import { Player, wavBlob } from "./audio.js";
import { LatestOnly, createEngine } from "./engine.js";
import { History } from "./history.js";
import { Log } from "./log.js";
import { drawWaveform } from "./plot.js";
import { encodeState, stateFromHash } from "./share.js";
import { defaultPage, openDocument, resetTab, stretchPage, tabState, withTabState } from "./document.js";
import { createBlobsTab } from "./blobs/tab.js";
import { createPaintedTab } from "./painted/tab.js";
import { clampDuration } from "./tracks/model.js";
import { createTracksTab } from "./tracks/tab.js";

const AUTOPLAY_MAX_S = 3; // longer sounds play on Play only (app.md, D10)

const $ = (id) => document.getElementById(id);
const ui = {
  play: $("play"), duration: $("duration"), autoplay: $("autoplay"), reset: $("reset"), undo: $("undo"), redo: $("redo"),
  open: $("open"), save: $("save"), link: $("link"), wav: $("wav"), file: $("file"),
  status: $("status"), versions: $("versions"), waveform: $("waveform"),
  log: $("log"), logToggle: $("log-toggle"), logLines: $("log-lines"), logCopy: $("log-copy"), logClear: $("log-clear"),
};

// --- the log ---------------------------------------------------------------------

const log = new Log();
log.onchange = () => {
  ui.logLines.replaceChildren(
    ...log.entries.map(({ time, level, text, detail }) => {
      const line = document.createElement("div");
      line.className = level;
      line.textContent = `${time} ${text}${detail ? `\n${detail.replace(/^/gm, "    ")}` : ""}`;
      return line;
    }),
  );
  ui.logLines.scrollTop = ui.logLines.scrollHeight;
  ui.logToggle.textContent = log.errors ? `Log (${log.errors})` : "Log";
  ui.logToggle.classList.toggle("has-errors", log.errors > 0);
};
window.addEventListener("error", (event) => log.error(`page error: ${event.message}`, event.error?.stack ?? ""));
window.addEventListener("unhandledrejection", (event) =>
  log.error(`page error: ${event.reason?.message ?? event.reason}`, event.reason?.stack ?? ""),
);

const engineKind = new URLSearchParams(location.search).get("engine") ?? "pyodide";
log.info(`page opened, engine: ${engineKind}`, navigator.userAgent);
let ready = false;
const engine = new LatestOnly(
  createEngine(engineKind, {
    onProgress: (text) => {
      status(text);
      log.info(text);
    },
    onReady: (versions) => {
      ready = true;
      log.info(`ready: ${versions}`);
      ui.versions.textContent = versions;
      ui.play.disabled = false;
      status("Ready. Draw, then press Play.");
      synthesize({ play: false });
    },
    onFailed: (message) => {
      status(`Could not start the synthesizer: ${message} (see Log)`, true);
      log.error(`could not start the synthesizer: ${message}`);
    },
  }),
);

const player = new Player();
let result = null; // {key, doc, sound}: the last sound made, from which tab's state

function status(text, error = false) {
  ui.status.textContent = text;
  ui.status.classList.toggle("error", error);
}

// --- the document and its history ----------------------------------------------

let initial = defaultPage();
try {
  const linked = stateFromHash(location.hash);
  if (linked) initial = openDocument(linked);
} catch (error) {
  log.error(`ignored the drawing in the link: ${error.message}`);
}
const history = new History(initial);
const commitFrom = (id) => (state) => change(withTabState(history.present, id, state));
const tabs = {
  tracks: createTracksTab($("tab-tracks"), { commit: commitFrom("tracks") }),
  painted: createPaintedTab($("tab-painted"), { commit: commitFrom("painted"), log }),
  blobs: createBlobsTab($("tab-blobs"), { commit: commitFrom("blobs") }),
};
// The tab shown is not an edit (undo does not switch tabs); it is saved with
// the document, so a link opens on the tab it was made on.
let tab = tabs[initial.tab] ?? tabs.tracks;
const tabButtons = [...document.querySelectorAll(".tabs [data-tab]")];

function showTab() {
  for (const button of tabButtons) {
    const active = button.dataset.tab === tab.id;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  }
  for (const id of Object.keys(tabs)) $(`tab-${id}`).hidden = id !== tab.id;
  // a tab that draws the result's waveform itself (the Modulation tab, in its Result box)
  document.querySelector("main > .result").hidden = Boolean(tab.ownWaveform);
  $("tab-caption").textContent = tabButtons.find((b) => b.dataset.tab === tab.id)?.dataset.caption ?? "";
}

function switchTab(id) {
  if (!tabs[id] || tabs[id] === tab) return;
  player.stop();
  tab.setPlayhead(null);
  tab = tabs[id];
  showTab();
  show();
  showResult();
  log.info(`switched to the ${id} tab`);
  if (ready) synthesize({ play: false });
}
for (const button of tabButtons) button.addEventListener("click", () => switchTab(button.dataset.tab));

// The document as saved and linked: with the tab shown.
const saved = () => ({ ...history.present, tab: tab.id });

function show() {
  const doc = history.present;
  tab.setDocument(tabState(doc, tab.id));
  ui.duration.value = doc.duration;
  ui.undo.disabled = !history.past.length;
  ui.redo.disabled = !history.future.length;
  window.history.replaceState(null, "", `${location.pathname}${location.search}#state=${encodeState(saved())}`);
}

// An edit has ended: keep it, and hear it if it is short enough.
function change(doc) {
  history.push(doc);
  show();
  afterChange();
}

function afterChange() {
  const short = history.present.duration <= AUTOPLAY_MAX_S;
  if (ready && short) synthesize({ play: ui.autoplay.checked });
  // a synthesis under way for the old drawing starts again on the new one
  else if (ready && running) synthesize({ play: running.play });
  else if (ready) status("Press Play to hear the change.");
}

// --- synthesis progress, over the tab's main figure ------------------------------

const progress = document.createElement("div");
progress.className = "synth-progress";
progress.innerHTML = `<div class="bar"></div><span class="label"></span>`;
let requests = 0; // counts synthesize() calls: only the newest shows its progress
let running = null; // {play} while a synthesis is under way

// fraction from 0 to 1, undefined while it is not known yet, null to hide
function showProgress(fraction) {
  const figure = tab.figure;
  if (fraction === null || !figure) return progress.remove();
  if (progress.parentNode !== figure) figure.appendChild(progress);
  const known = typeof fraction === "number";
  progress.classList.toggle("unknown", !known);
  progress.querySelector(".bar").style.width = known ? `${Math.round(100 * fraction)}%` : "";
  progress.querySelector(".label").textContent = known ? `Synthesizing… ${Math.round(100 * fraction)}%` : "Synthesizing…";
}

// --- synthesis and playback ----------------------------------------------------

async function synthesize({ play }) {
  const doc = history.present;
  const asked = tab;
  const state = tabState(doc, tab.id);
  const key = `${tab.id} ${JSON.stringify(state)}`;
  const mine = ++requests;
  if (result?.key === key) {
    running = null;
    showProgress(null);
    if (play) start(result.sound);
    return result.sound;
  }
  const blocked = tab.blocked?.();
  if (blocked) {
    running = null;
    showProgress(null);
    result = null;
    showResult();
    status(blocked);
    return null;
  }
  status(doc.duration > 1 ? `Synthesizing ${doc.duration} s…` : "Synthesizing…");
  running = { play };
  showProgress(undefined);
  let sound;
  try {
    sound = await engine.synthesize({ tab: tab.id, state }, (fraction) => mine === requests && showProgress(fraction));
  } catch (error) {
    if (mine !== requests) return null; // a newer drawing is being made; this one's failure no longer matters
    running = null;
    showProgress(null);
    status(`Synthesis failed: ${error.message} (see Log; Reset starts again)`, true);
    log.error(`synthesis failed: ${error.message}`, error.detail ?? "");
    if (tab === asked && history.present === doc) tab.failed?.(error.message);
    return null;
  }
  if (mine === requests) {
    running = null;
    showProgress(null);
  }
  if (!sound) return null; // a newer drawing replaced this request
  // The drawing changed while this was made, to one that asks for no sound
  // (nothing drawn) or to another tab: this sound is no longer what is shown.
  if (tab !== asked || history.present !== doc) return null;
  result = { key, doc, sound };
  showResult();
  status(`Made ${doc.duration} s in ${sound.synthesisSeconds.toFixed(2)} s.`);
  log.info(`made ${doc.duration} s in ${sound.synthesisSeconds.toFixed(2)} s`);
  if (play && history.present === doc) start(sound);
  return sound;
}

function showResult() {
  if (result && !result.key.startsWith(`${tab.id} `)) result = null;
  const sound = result?.sound;
  const duration = result?.doc.duration ?? history.present.duration;
  tab.setResult(sound);
  drawWaveform(ui.waveform, sound?.samples, sound?.fs, duration);
  ui.wav.disabled = !sound;
}

function start(sound) {
  player.play(sound.samples, sound.fs);
  ui.play.textContent = "■ Stop";
  const tick = () => {
    const t = player.position;
    tab.setPlayhead(t);
    if (t !== null) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

player.onended = () => {
  ui.play.textContent = "▶ Play";
  tab.setPlayhead(null);
};

async function togglePlay() {
  if (player.playing) return player.stop();
  if (!ready) return status("Still loading; Play will work once sonore is ready.");
  await synthesize({ play: true });
}

// --- controls --------------------------------------------------------------------

ui.play.addEventListener("click", togglePlay);

ui.duration.addEventListener("change", () => {
  const duration = clampDuration(Number(ui.duration.value) || history.present.duration);
  if (duration === history.present.duration) return (ui.duration.value = duration);
  change(stretchPage(history.present, duration));
});

function undo() {
  if (history.undo()) {
    show();
    afterChange();
  }
}
function redo() {
  if (history.redo()) {
    show();
    afterChange();
  }
}
ui.undo.addEventListener("click", undo);
// Reset is an edit like any other, so Undo brings the drawing back.
ui.reset.addEventListener("click", () => {
  change(resetTab(history.present, tab.id));
  log.info(`reset the ${tab.id} tab to its default drawing`);
  if (!ready) status("Reset to the default drawing.");
});
ui.redo.addEventListener("click", redo);

function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

ui.save.addEventListener("click", () => {
  const text = JSON.stringify(saved(), null, 1);
  download(new Blob([text], { type: "application/json" }), "sketch.json");
});
ui.wav.addEventListener("click", () => {
  if (result) download(wavBlob(result.sound.samples, result.sound.fs), "sketch.wav");
});
ui.open.addEventListener("click", () => ui.file.click());
ui.file.addEventListener("change", async () => {
  const file = ui.file.files[0];
  ui.file.value = "";
  if (!file) return;
  try {
    change(openDocument(JSON.parse(await file.text())));
    status(`Opened ${file.name}.`);
    log.info(`opened ${file.name}`);
  } catch (error) {
    status(`Could not open ${file.name}: ${error.message}`, true);
    log.error(`could not open ${file.name}: ${error.message}`);
  }
});
ui.link.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(location.href);
    status("Link copied: it opens this drawing.");
  } catch {
    status("The address bar holds the link to this drawing.");
  }
});

ui.logToggle.addEventListener("click", () => {
  ui.log.hidden = !ui.log.hidden;
  ui.logToggle.setAttribute("aria-expanded", String(!ui.log.hidden));
  if (!ui.log.hidden) ui.logLines.scrollTop = ui.logLines.scrollHeight;
});
ui.logClear.addEventListener("click", () => log.clear());
ui.logCopy.addEventListener("click", async () => {
  const report = [
    `sonore sketch log, ${new Date().toISOString()}`,
    `versions: ${ui.versions.textContent || "(not loaded)"}`,
    `engine: ${engineKind}`,
    `browser: ${navigator.userAgent}`,
    "",
    log.text(),
    "",
    "current drawing:",
    JSON.stringify(saved()),
  ].join("\n");
  try {
    await navigator.clipboard.writeText(report);
    status("Log copied, with the versions and the current drawing.");
  } catch {
    status("Could not copy; select the log text instead.", true);
  }
});

document.addEventListener("keydown", (event) => {
  if (event.target.matches?.("input[type=number], input[type=text]")) return;
  const mod = event.ctrlKey || event.metaKey;
  if (mod && event.key.toLowerCase() === "z") {
    event.preventDefault();
    return event.shiftKey ? redo() : undo();
  }
  if (mod && event.key.toLowerCase() === "y") {
    event.preventDefault();
    return redo();
  }
  if (mod || event.altKey) return;
  if (event.key === " ") {
    event.preventDefault();
    return togglePlay();
  }
  if (tab.key(event)) event.preventDefault();
});

new ResizeObserver(showResult).observe(ui.waveform);
showTab();
show();
