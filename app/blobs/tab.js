// The Modulation tab: place Gaussian blobs on rate x density and hear a sound
// whose envelopes have that modulation spectrum (docs/design/tabs/blobs.md).
//
// The plane shows the drawn spectrum itself, on the grid sonore puts it on
// (rate steps of 1/duration), computed here with sonore's formula so it
// follows a drag at once; each blob's outline (one standard deviation), its
// centre and, for the selected blob, its two width handles go on top. An
// edit is one gesture: adding, moving or resizing a blob is committed when
// the pointer comes up.

import { magma } from "../colormap.js";
import { fitCanvas } from "../plot.js";
import {
  CARRIERS,
  COARSE_BELOW_S,
  DENSITY_MAX,
  MAX_BLOBS,
  NEW_BLOB,
  clampDensity,
  clampRate,
  clampWidth,
  depthThatFits,
  grid,
  power,
  rateToUnit,
  tidy,
  unitToRate,
} from "./model.js";

const MARGIN = { left: 52, right: 10, top: 8, bottom: 36 };
const SEAM = 7; // half the gap between the two sides of the rate axis, px
const FLOOR_DB = -40; // the picture's range below the drawing's peak
const PICK_PX = 8;
const RATE_TICKS = [1, 2, 4, 8, 16, 32, 64];

export function createBlobsTab(root, { commit }) {
  let state = null;
  let selected = null; // index of the selected blob
  let drag = null; // {kind, index, items, changed, added} while a gesture lasts
  let fits = null; // the depth sonore said fits, after it refused this one

  root.innerHTML = `
    <div class="blobs-body">
      <div class="paint-area"><canvas class="plane"></canvas></div>
      <aside class="side">
        <fieldset class="blob-fields"><legend>Blob</legend>
          <p class="hint blob-count"></p>
          <div class="blob-edit">
            <label class="field" title="Temporal modulation rate; negative sweeps up, positive sweeps down">Rate <input type="number" class="rate" step="0.1"> Hz</label>
            <label class="field" title="Spectral modulation density">Density <input type="number" class="density" min="0" max="${DENSITY_MAX}" step="0.05"> cyc/oct</label>
            <label class="field" title="Standard deviation along rate, in octaves of rate">Width <input type="number" class="rate-width" min="0.05" max="3" step="0.05"> oct</label>
            <label class="field" title="Standard deviation along density">Height <input type="number" class="density-width" min="0.05" max="3" step="0.05"> cyc/oct</label>
            <label class="field" title="Peak power relative to the other blobs">Level <input type="number" class="level" min="-40" max="0" step="1"> dB</label>
            <button type="button" class="delete" title="Remove this blob (Delete)">Delete</button>
          </div>
        </fieldset>
        <fieldset><legend>Sound</legend>
          <label class="field" title="What carries the modulation: log-spaced tones (clearest) or noise (adds modulation of its own)">Carrier
            <select class="carrier">${CARRIERS.map((c) => `<option value="${c}">${c}</option>`).join("")}</select></label>
          <label class="field" title="How deep the modulation is: the envelopes' rms about their mean, relative to it">Depth <input type="number" class="depth" min="0.01" max="1" step="0.01"></label>
          <button type="button" class="use-depth" hidden></button>
          <label class="field" title="Which random draw of the modulation's timing to hear">Seed <input type="number" class="seed" step="1"></label>
          <button type="button" class="new-draw" title="Hear another draw with the same spectrum">New draw</button>
          <button type="button" class="clear" title="Remove every blob (Undo brings them back)">Clear</button>
        </fieldset>
        <p class="hint coarse" hidden></p>
        <p class="hint">Click to add a blob, drag to move it, drag its squares to change its width and height. Space plays.</p>
      </aside>
    </div>`;
  const $ = (selector) => root.querySelector(selector);
  const canvas = $("canvas.plane");
  const ui = {
    count: $(".blob-count"), edit: $(".blob-edit"), rate: $(".rate"), density: $(".density"),
    rateWidth: $(".rate-width"), densityWidth: $(".density-width"), level: $(".level"), remove: $(".delete"),
    carrier: $(".carrier"), depth: $(".depth"), useDepth: $(".use-depth"), seed: $(".seed"),
    newDraw: $(".new-draw"), clear: $(".clear"), coarse: $(".coarse"),
  };

  const items = () => drag?.items ?? state.items;

  function commitItems(next, changes = {}) {
    commit({ ...state, ...changes, items: next });
  }

  // --- the side panel ------------------------------------------------------------

  function showSettings() {
    const list = items();
    if (selected !== null && selected >= list.length) selected = list.length ? list.length - 1 : null;
    const blob = selected === null ? null : list[selected];
    ui.edit.hidden = !blob;
    ui.count.textContent =
      list.length >= MAX_BLOBS
        ? `${list.length} of ${MAX_BLOBS} blobs: delete one to add another.`
        : `${list.length} of ${MAX_BLOBS} blobs.${blob ? "" : " Click a blob to edit it, or empty space to add one."}`;
    if (blob) {
      ui.rate.value = blob.rate;
      ui.density.value = blob.density;
      ui.rateWidth.value = blob.rate_width;
      ui.densityWidth.value = blob.density_width;
      ui.level.value = blob.level;
    }
    ui.carrier.value = state.carrier;
    ui.depth.value = state.rms_depth;
    ui.seed.value = state.seed;
    ui.useDepth.hidden = fits === null;
    if (fits !== null) ui.useDepth.textContent = `Use depth ${fits}`;
    const { rateStep } = grid(state);
    ui.coarse.hidden = state.duration >= COARSE_BELOW_S;
    ui.coarse.textContent = `At ${state.duration} s, rates come in steps of ${+rateStep.toFixed(2)} Hz, coarse below about 8 Hz; ${COARSE_BELOW_S} s or more shows low rates finer.`;
  }

  function editSelected(key, clamp) {
    return () => {
      const blob = state.items[selected];
      const value = Number(ui[fieldOf[key]].value);
      if (!blob || !Number.isFinite(value) || (key === "rate" && value === 0)) return showSettings();
      const next = tidy(clamp(value));
      if (next === blob[key]) return showSettings();
      commitItems(state.items.map((b, i) => (i === selected ? { ...b, [key]: next } : b)));
    };
  }
  const fieldOf = { rate: "rate", density: "density", rate_width: "rateWidth", density_width: "densityWidth", level: "level" };
  ui.rate.addEventListener("change", editSelected("rate", clampRate));
  ui.density.addEventListener("change", editSelected("density", clampDensity));
  ui.rateWidth.addEventListener("change", editSelected("rate_width", clampWidth));
  ui.densityWidth.addEventListener("change", editSelected("density_width", clampWidth));
  ui.level.addEventListener("change", editSelected("level", (x) => Math.min(0, Math.max(-40, x))));
  ui.remove.addEventListener("click", removeSelected);

  ui.carrier.addEventListener("change", () => commit({ ...state, carrier: ui.carrier.value }));
  ui.depth.addEventListener("change", () => {
    const depth = tidy(Number(ui.depth.value));
    if (depth > 0 && depth <= 1 && depth !== state.rms_depth) commit({ ...state, rms_depth: depth });
    else showSettings();
  });
  ui.useDepth.addEventListener("click", () => fits !== null && commit({ ...state, rms_depth: fits }));
  ui.seed.addEventListener("change", () => {
    const seed = Math.round(Number(ui.seed.value));
    if (Number.isFinite(seed) && seed !== state.seed) commit({ ...state, seed });
    else showSettings();
  });
  ui.newDraw.addEventListener("click", () => commit({ ...state, seed: state.seed + 1 }));
  ui.clear.addEventListener("click", () => state.items.length && commitItems([]));

  function removeSelected() {
    if (selected === null || !state.items[selected]) return false;
    const next = state.items.filter((_, i) => i !== selected);
    selected = next.length ? Math.min(selected, next.length - 1) : null;
    commitItems(next);
    return true;
  }

  // --- the plane -------------------------------------------------------------------

  function geometry() {
    const width = canvas.clientWidth || 600;
    const height = canvas.clientHeight || 300;
    const x0 = MARGIN.left;
    const x1 = width - MARGIN.right;
    const y0 = MARGIN.top;
    const y1 = height - MARGIN.bottom;
    const xc = (x0 + x1) / 2;
    const half = xc - SEAM - x0;
    return {
      width, height, x0, x1, y0, y1, xc,
      x: (rate) => (rate > 0 ? xc + SEAM + rateToUnit(rate) * half : xc - SEAM + rateToUnit(rate) * half),
      y: (density) => y1 - (density / DENSITY_MAX) * (y1 - y0),
      // the rate at a pixel; the seam's pixels go to the nearer side's 1 Hz
      rate: (px) => (px >= xc ? unitToRate(Math.max(0, (px - xc - SEAM) / half)) : -unitToRate(Math.max(0, (xc - SEAM - px) / half))),
      density: (py) => ((y1 - py) / (y1 - y0)) * DENSITY_MAX,
    };
  }

  // A blob's outline in pixels: centre, the ellipse's extent, and its two handles.
  function shape(g, blob) {
    const xl = g.x(blob.rate * 2 ** -blob.rate_width);
    const xr = g.x(blob.rate * 2 ** blob.rate_width);
    return {
      cx: g.x(blob.rate),
      cy: g.y(blob.density),
      ex: (xl + xr) / 2,
      rx: Math.max(2, Math.abs(xr - xl) / 2),
      ry: Math.max(2, (blob.density_width / DENSITY_MAX) * (g.y1 - g.y0)),
      widthHandle: [xr, g.y(blob.density)],
      heightHandle: [g.x(blob.rate), g.y(blob.density + blob.density_width)],
    };
  }

  const image = document.createElement("canvas");

  // The drawn spectrum, one pixel per CSS pixel of the plot, each pixel
  // showing the grid cell (rate, density) it falls in.
  function picture(g) {
    const width = Math.max(1, Math.round(g.x1 - g.x0));
    const height = Math.max(1, Math.round(g.y1 - g.y0));
    image.width = width;
    image.height = height;
    const context = image.getContext("2d");
    const pixels = context.createImageData(width, height);
    const { rateStep, densityStep, densities } = grid(state);
    const list = items();
    // each pixel row's density cell, or -1 above the grid's last
    const rowCell = Int32Array.from({ length: height }, (_, py) => {
      const j = Math.round(g.density(g.y0 + py + 0.5) / densityStep);
      return j < densities.length ? j : -1;
    });
    const columns = [];
    let peak = 0;
    for (let px = 0; px < width; px++) {
      const x = g.x0 + px + 0.5;
      const k = Math.abs(x - g.xc) < SEAM ? 0 : Math.round(g.rate(x) / rateStep);
      if (k === 0) {
        columns.push(null);
        continue;
      }
      const column = densities.map((d) => power(list, k * rateStep, d));
      for (const p of column) peak = Math.max(peak, p);
      columns.push(column);
    }
    const floor = magma(0);
    for (let px = 0; px < width; px++) {
      const column = columns[px];
      for (let py = 0; py < height; py++) {
        const i = 4 * (py * width + px);
        const j = rowCell[py];
        let colour = floor;
        if (column && j >= 0 && peak > 0) {
          const level = 10 * Math.log10(column[j] / peak);
          colour = magma(Math.max(0, 1 - level / FLOOR_DB));
        }
        pixels.data.set(colour, i);
        pixels.data[i + 3] = column || Math.abs(g.x0 + px + 0.5 - g.xc) >= SEAM ? 255 : 0;
      }
    }
    context.putImageData(pixels, 0, 0);
    return image;
  }

  function render() {
    if (!state) return;
    const context = fitCanvas(canvas);
    const ratio = canvas.width / (canvas.clientWidth || 1);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    const g = geometry();
    const style = getComputedStyle(canvas);
    const muted = style.getPropertyValue("--muted").trim() || "#6b7280";
    const line = style.getPropertyValue("--line").trim() || "#d5d9e0";
    context.clearRect(0, 0, g.width, g.height);
    context.imageSmoothingEnabled = false;
    context.drawImage(picture(g), g.x0, g.y0, g.x1 - g.x0, g.y1 - g.y0);

    // axes and gridlines
    context.lineWidth = 1;
    context.font = "11px system-ui, sans-serif";
    context.fillStyle = muted;
    context.strokeStyle = line;
    context.strokeRect(g.x0 + 0.5, g.y0 + 0.5, g.x1 - g.x0 - 1, g.y1 - g.y0 - 1);
    context.textAlign = "right";
    context.textBaseline = "middle";
    for (let d = 0; d <= DENSITY_MAX; d++) {
      const y = Math.round(g.y(d)) + 0.5;
      context.strokeStyle = "rgba(255, 255, 255, 0.15)";
      context.beginPath();
      context.moveTo(g.x0, y);
      context.lineTo(g.x1, y);
      context.stroke();
      context.fillText(`${d}`, g.x0 - 6, Math.min(Math.max(y, g.y0 + 5), g.y1 - 5));
    }
    context.save();
    context.translate(12, (g.y0 + g.y1) / 2);
    context.rotate(-Math.PI / 2);
    context.textAlign = "center";
    context.fillText("cyc/oct", 0, 0);
    context.restore();
    context.textAlign = "center";
    context.textBaseline = "top";
    for (const sign of [-1, 1]) {
      for (const r of RATE_TICKS) {
        const x = Math.round(g.x(sign * r)) + 0.5;
        context.strokeStyle = "rgba(255, 255, 255, 0.15)";
        context.beginPath();
        context.moveTo(x, g.y0);
        context.lineTo(x, g.y1);
        context.stroke();
        context.fillText(`${sign * r}`.replace("-", "−"), x, g.y1 + 4);
      }
    }
    context.textAlign = "left";
    context.fillText("← sweeps up", g.x0, g.y1 + 19);
    context.textAlign = "center";
    context.fillText("rate, Hz", g.xc, g.y1 + 19);
    context.textAlign = "right";
    context.fillText("sweeps down →", g.x1, g.y1 + 19);

    // the blobs
    items().forEach((blob, i) => {
      const s = shape(g, blob);
      const chosen = i === selected;
      context.strokeStyle = chosen ? "rgba(255, 255, 255, 0.95)" : "rgba(255, 255, 255, 0.6)";
      context.lineWidth = chosen ? 2 : 1.25;
      context.setLineDash(chosen ? [] : [4, 3]);
      context.beginPath();
      context.ellipse(s.ex, s.cy, s.rx, s.ry, 0, 0, 2 * Math.PI);
      context.stroke();
      context.setLineDash([]);
      context.fillStyle = chosen ? "#ffffff" : "rgba(255, 255, 255, 0.8)";
      context.beginPath();
      context.arc(s.cx, s.cy, chosen ? 4.5 : 3.5, 0, 2 * Math.PI);
      context.fill();
      if (chosen) {
        context.fillStyle = "#ffffff";
        context.strokeStyle = "#000000";
        context.lineWidth = 1;
        for (const [hx, hy] of [s.widthHandle, s.heightHandle]) {
          context.fillRect(hx - 4, hy - 4, 8, 8);
          context.strokeRect(hx - 4 + 0.5, hy - 4 + 0.5, 7, 7);
        }
      }
    });
  }

  // --- gestures --------------------------------------------------------------------

  function local(event) {
    const box = canvas.getBoundingClientRect();
    return [event.clientX - box.left, event.clientY - box.top];
  }

  // What is under the pointer: the selected blob's handles first, then the
  // nearest centre, then the inside of the smallest outline.
  function pick(g, [px, py]) {
    const list = items();
    const near = (x, y) => Math.hypot(px - x, py - y) <= PICK_PX;
    if (selected !== null && list[selected]) {
      const s = shape(g, list[selected]);
      if (near(...s.widthHandle)) return { kind: "rate_width", index: selected };
      if (near(...s.heightHandle)) return { kind: "density_width", index: selected };
    }
    let best = null;
    list.forEach((blob, index) => {
      const s = shape(g, blob);
      const distance = Math.hypot(px - s.cx, py - s.cy);
      if (distance <= PICK_PX && (!best || distance < best.distance)) best = { kind: "move", index, distance };
    });
    if (best) return best;
    let inside = null;
    list.forEach((blob, index) => {
      const s = shape(g, blob);
      const area = s.rx * s.ry;
      if (((px - s.ex) / s.rx) ** 2 + ((py - s.cy) / s.ry) ** 2 <= 1 && (!inside || area < inside.area)) {
        inside = { kind: "move", index, area };
      }
    });
    return inside;
  }

  const inPlot = (g, [px, py]) => px >= g.x0 && px <= g.x1 && py >= g.y0 && py <= g.y1;

  canvas.addEventListener("pointerdown", (event) => {
    if (!state || event.button !== 0) return;
    const g = geometry();
    const at = local(event);
    if (!inPlot(g, at)) return;
    event.preventDefault();
    let hit = pick(g, at);
    let list = state.items.map((blob) => ({ ...blob }));
    let added = false;
    if (!hit) {
      if (list.length >= MAX_BLOBS) {
        selected = null;
        showSettings();
        return render();
      }
      list = [...list, { rate: tidy(clampRate(g.rate(at[0]))), density: tidy(clampDensity(g.density(at[1]))), ...NEW_BLOB }];
      hit = { kind: "move", index: list.length - 1 };
      added = true;
    }
    canvas.setPointerCapture(event.pointerId);
    selected = hit.index;
    const blob = list[hit.index];
    // a move keeps the blob's centre where it was relative to the pointer
    drag = { ...hit, items: list, added, changed: false, offset: [at[0] - g.x(blob.rate), at[1] - g.y(blob.density)] };
    showSettings();
    render();
  });

  canvas.addEventListener("pointermove", (event) => {
    if (!state) return;
    const g = geometry();
    const at = local(event);
    if (!drag) {
      const hit = inPlot(g, at) ? pick(g, at) : null;
      canvas.style.cursor = !hit ? "crosshair" : hit.kind === "move" ? "grab" : hit.kind === "rate_width" ? "ew-resize" : "ns-resize";
      return;
    }
    const blob = drag.items[drag.index];
    let next = blob;
    if (drag.kind === "move") {
      const x = at[0] - drag.offset[0];
      const y = at[1] - drag.offset[1];
      next = { ...blob, rate: tidy(clampRate(g.rate(x))), density: tidy(clampDensity(g.density(y))) };
    } else if (drag.kind === "rate_width") {
      const octaves = Math.abs(Math.log2(Math.abs(g.rate(at[0])) / Math.abs(blob.rate)));
      next = { ...blob, rate_width: tidy(clampWidth(octaves)) };
    } else {
      next = { ...blob, density_width: tidy(clampWidth(Math.abs(g.density(at[1]) - blob.density))) };
    }
    if (next.rate !== blob.rate || next.density !== blob.density || next.rate_width !== blob.rate_width || next.density_width !== blob.density_width) {
      drag.items = drag.items.map((b, i) => (i === drag.index ? next : b));
      drag.changed = true;
      showSettings();
      render();
    }
  });

  function finish(event) {
    if (!drag) return;
    const { items: next, added, changed } = drag;
    drag = null;
    if (event.type === "pointercancel" || !(added || changed)) {
      showSettings();
      return render();
    }
    commitItems(next);
  }
  canvas.addEventListener("pointerup", finish);
  canvas.addEventListener("pointercancel", finish);

  new ResizeObserver(render).observe(canvas);

  return {
    id: "blobs",
    setDocument(next) {
      fits = null; // a refusal is shown again if this drawing is refused again
      drag = null;
      state = next;
      showSettings();
      render();
    },
    setResult(sound) {
      if (sound) {
        fits = null;
        showSettings();
      }
    },
    setPlayhead() {},
    // sonore refused the drawing; if it named a depth that fits, offer a
    // little less: it prints the depth rounded, and the depth that fits can
    // move by a few thousandths with the depth asked for (seen in
    // tools/check_page.py: 0.27 named, then 0.261 at 0.27). If the offer is
    // refused too, the next refusal offers again.
    failed(message) {
      const depth = depthThatFits(message);
      fits = depth === null ? null : Math.max(0.01, Math.floor((depth - 0.005) * 100) / 100);
      showSettings();
    },
    blocked() {
      return state.items.length ? null : "No blobs yet: click the plane to add one.";
    },
    key(event) {
      if (event.key === "Delete" || event.key === "Backspace") return removeSelected();
      return false;
    },
  };
}
