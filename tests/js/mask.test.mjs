import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { test } from "node:test";

import { decodeLevels } from "../../app/painted/model.js";
import { defaultPage, forLink, openDocument, tabState, upgrade, withRecording, withTabState } from "../../app/document.js";
import { encodePcm16 } from "../../app/edit/model.js";
import { BLANK_LEVELS, COLUMNS, FLOOR_DB, ROWS, WINDOW_S, blank, check, rowFrequency } from "../../app/mask/model.js";

function python(code) {
  return execFileSync("python", ["-c", `import sys; sys.path.insert(0, "src")\nfrom sonore_sketch import mask\n${code}`], { encoding: "utf8" }).trim();
}

test("the grid and the starting mask are the Python half's", async () => {
  const [rows, columns, floor, window, f0, fLast] = JSON.parse(
    python("import json; f = mask.row_frequencies(16000); print(json.dumps([mask.ROWS, mask.COLUMNS, mask.FLOOR_DB, mask.WINDOW_S, f[0], f[-1]]))"),
  );
  assert.deepEqual([rows, columns, floor, window], [ROWS, COLUMNS, FLOOR_DB, WINDOW_S]);
  assert.equal(rowFrequency(0, 16000), f0);
  assert.equal(rowFrequency(ROWS - 1, 16000), fLast);
  assert.equal(BLANK_LEVELS, python("print(mask.BLANK_LEVELS)"));
  assert.deepEqual(await decodeLevels(BLANK_LEVELS, ROWS * COLUMNS), blank());
});

test("the page carries the mask section, with the source's drawing in its state", () => {
  const page = defaultPage();
  check(tabState(page, "mask"));
  const old = { ...page };
  delete old.mask;
  assert.deepEqual(upgrade(old).mask, page.mask);
  const speech = withTabState(page, "mask", { ...tabState(page, "mask"), source: "speech" });
  assert.deepEqual(tabState(speech, "mask").speech, page.tracks);
  assert.equal(withTabState(speech, "mask", tabState(speech, "mask")).mask.speech, undefined);
  assert.equal(speech.edit.source, page.edit.source); // the two tabs choose their sources apart
});

test("a recording opened here is this tab's source, shared with the Edit tab, and never in links", () => {
  const recording = { name: "a.wav", fs: 16000, pcm16: encodePcm16(Float32Array.from({ length: 8000 }, (_, i) => Math.sin(i / 7))) };
  const page = withRecording(defaultPage(), recording, 0.5, "mask");
  assert.equal(page.duration, 0.5);
  assert.equal(page.mask.source, "file");
  assert.equal(page.edit.source, "syllables");
  assert.equal(tabState(page, "mask").recording, recording);
  assert.equal(tabState(withTabState(page, "edit", { ...tabState(page, "edit"), source: "file" }), "edit").recording, recording);
  assert.equal(tabState(openDocument(forLink(page)), "mask").recording, undefined);
});

test("bad sections are refused", () => {
  const state = tabState(defaultPage(), "mask");
  assert.throws(() => check({ ...state, source: "radio" }), /source/);
  assert.throws(() => check({ ...state, rows: 128 }), /256 rows/);
  assert.throws(() => check({ ...state, window: 0.005 }), /window/);
  assert.throws(() => openDocument({ ...defaultPage(), mask: { ...state, columns: 3 } }), /256 columns/);
});
