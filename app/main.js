// The page shell: tabs, duration, synthesis engine, playback, the result,
// undo, save, open and links (docs/design/app.md, "One tab, one route back
// to sound"). Tabs plug in through a small contract: a document to edit, a
// `commit` callback when an edit ends, and a picture of the last result.

import { Player, wavBlob } from "./audio.js";
import { LatestOnly, createEngine } from "./engine.js";
import { History } from "./history.js";
import { drawSpectrogram, drawWaveform } from "./plot.js";
import { encodeState, stateFromHash } from "./share.js";
import { check, clampDuration, defaultDocument, stretch } from "./tracks/model.js";
import { createTracksTab } from "./tracks/tab.js";

const AUTOPLAY_MAX_S = 3; // longer sounds play on Play only (app.md, D10)

const $ = (id) => document.getElementById(id);
const ui = {
  play: $("play"), duration: $("duration"), autoplay: $("autoplay"), undo: $("undo"), redo: $("redo"),
  open: $("open"), save: $("save"), link: $("link"), wav: $("wav"), file: $("file"),
  status: $("status"), versions: $("versions"), waveform: $("waveform"), spectrogram: $("spectrogram"),
};

const engineKind = new URLSearchParams(location.search).get("engine") ?? "pyodide";
let ready = false;
const engine = new LatestOnly(
  createEngine(engineKind, {
    onProgress: (text) => status(text),
    onReady: (versions) => {
      ready = true;
      ui.versions.textContent = versions;
      ui.play.disabled = false;
      status("Ready. Draw on a track, then press Play.");
      synthesize({ play: false });
    },
    onFailed: (message) => status(`Could not start the synthesizer: ${message}`, true),
  }),
);

const player = new Player();
let result = null; // {doc, sound}: the last sound made, and from which document

function status(text, error = false) {
  ui.status.textContent = text;
  ui.status.classList.toggle("error", error);
}

// --- the document and its history ----------------------------------------------

let initial = defaultDocument();
try {
  const linked = stateFromHash(location.hash);
  if (linked) initial = check(linked);
} catch (error) {
  console.warn("ignoring the link's drawing:", error);
}
const history = new History(initial);
const tab = createTracksTab($("tab-tracks"), { commit: (doc) => change(doc) });

function show() {
  const doc = history.present;
  tab.setDocument(doc);
  ui.duration.value = doc.duration;
  ui.undo.disabled = !history.past.length;
  ui.redo.disabled = !history.future.length;
  window.history.replaceState(null, "", `${location.pathname}${location.search}#state=${encodeState(doc)}`);
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
  else if (ready) status("Press Play to hear the change.");
}

// --- synthesis and playback ----------------------------------------------------

async function synthesize({ play }) {
  const doc = history.present;
  if (result?.doc === doc) {
    if (play) start(result.sound);
    return result.sound;
  }
  status(doc.duration > 1 ? `Synthesizing ${doc.duration} s…` : "Synthesizing…");
  let sound;
  try {
    sound = await engine.synthesize({ tab: tab.id, state: doc });
  } catch (error) {
    status(`Synthesis failed: ${error.message}`, true);
    return null;
  }
  if (!sound) return null; // a newer drawing replaced this request
  result = { doc, sound };
  showResult();
  status(`Made ${doc.duration} s in ${sound.synthesisSeconds.toFixed(2)} s.`);
  if (play && history.present === doc) start(sound);
  return sound;
}

function showResult() {
  const sound = result?.sound;
  const duration = result?.doc.duration ?? history.present.duration;
  tab.setResult(sound);
  drawWaveform(ui.waveform, sound?.samples, sound?.fs, duration);
  drawSpectrogram(ui.spectrogram, sound?.spectrogram, duration, sound?.fs / 2 || 8000);
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
  change(stretch(history.present, duration));
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
ui.redo.addEventListener("click", redo);

function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

ui.save.addEventListener("click", () => {
  const text = JSON.stringify(history.present, null, 1);
  download(new Blob([text], { type: "application/json" }), "tracks.json");
});
ui.wav.addEventListener("click", () => {
  if (result) download(wavBlob(result.sound.samples, result.sound.fs), "tracks.wav");
});
ui.open.addEventListener("click", () => ui.file.click());
ui.file.addEventListener("change", async () => {
  const file = ui.file.files[0];
  ui.file.value = "";
  if (!file) return;
  try {
    change(check(JSON.parse(await file.text())));
    status(`Opened ${file.name}.`);
  } catch (error) {
    status(`Could not open ${file.name}: ${error.message}`, true);
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
show();
