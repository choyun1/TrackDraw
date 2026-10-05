import assert from "node:assert/strict";
import { test } from "node:test";

import { History } from "../../app/history.js";
import { decodeState, encodeState, stateFromHash } from "../../app/share.js";
import {
  check,
  clampDuration,
  clampValue,
  defaultDocument,
  insertPoint,
  movePoint,
  nearestPoint,
  points,
  replaceSpan,
  simplify,
  stretch,
  tidyDocument,
  valueAt,
  withPoints,
} from "../../app/tracks/model.js";

test("a number is a flat track over the whole duration", () => {
  const doc = defaultDocument();
  assert.deepEqual(points(doc, "F4"), [[0, 3500], [0.6, 3500]]);
  assert.deepEqual(points({ ...doc, params: {} }, "B3"), [[0, 150], [0.6, 150]]);
});

test("withPoints stores [times, values], sorted, and leaves the old document alone", () => {
  const doc = defaultDocument();
  const next = withPoints(doc, "F4", [[0.5, 3600], [0.1, 3400]]);
  assert.deepEqual(next.params.F4, [[0.1, 0.5], [3400, 3600]]);
  assert.equal(doc.params.F4, 3500);
});

test("valueAt interpolates linearly and holds beyond the ends, as sonore does", () => {
  const pts = [[0.1, 100], [0.3, 300]];
  assert.equal(valueAt(pts, 0), 100);
  assert.equal(valueAt(pts, 0.2), 200);
  assert.equal(valueAt(pts, 1), 300);
});

test("point edits: grab within tolerance, insert in order, move between neighbours", () => {
  const pts = [[0, 1], [0.2, 2], [0.4, 3]];
  assert.equal(nearestPoint(pts, 0.21, 0.02), 1);
  assert.equal(nearestPoint(pts, 0.3, 0.02), -1);
  const { pts: added, index } = insertPoint(pts, 0.3, 9);
  assert.equal(index, 2);
  assert.deepEqual(added.map(([t]) => t), [0, 0.2, 0.3, 0.4]);
  // Kept 0.1 ms inside its neighbours: sonore needs times to increase.
  const [right] = movePoint(pts, 1, 0.9, 5)[1];
  const [left] = movePoint(pts, 1, -1, 5)[1];
  assert.ok(Math.abs(right - 0.3999) < 1e-12 && Math.abs(left - 0.0001) < 1e-12);
});

test("a line replaces the breakpoints under it, as the paper's line-draw", () => {
  const pts = [[0, 1], [0.1, 2], [0.2, 3], [0.3, 4]];
  assert.deepEqual(replaceSpan(pts, [[0.05, 10], [0.25, 20]]), [[0, 1], [0.05, 10], [0.25, 20], [0.3, 4]]);
});

test("freehand strokes simplify to the fewest breakpoints within the tolerance", () => {
  const ramp = Array.from({ length: 50 }, (_, i) => [i / 49, 1000 + 500 * (i / 49)]);
  assert.deepEqual(simplify(ramp, 1), [ramp[0], ramp[49]]);
  // A corner survives.
  const corner = Array.from({ length: 51 }, (_, i) => [i / 50, i <= 25 ? 1000 : 1000 + 40 * (i - 25)]);
  const kept = simplify(corner, 5);
  assert.equal(kept.length, 3);
  assert.deepEqual(kept[1], corner[25]);
  // Every original point is within the tolerance of the simplified track.
  for (const [t, v] of corner) assert.ok(Math.abs(valueAt(kept, t) - v) <= 5);
});

test("stretching scales breakpoint times exactly and keeps values (tracks.md, C3)", () => {
  const doc = defaultDocument();
  const longer = stretch(doc, 1.2);
  assert.equal(longer.duration, 1.2);
  assert.deepEqual(longer.params.F1[0], doc.params.F1[0].map((t) => t * 2));
  assert.deepEqual(longer.params.F1[1], doc.params.F1[1]);
  assert.equal(longer.params.F4, 3500);
  assert.equal(clampDuration(30), 10);
  assert.equal(clampDuration(0), 0.05);
});

test("check accepts the default document and refuses broken ones", () => {
  assert.equal(check(defaultDocument()).trackdraw, 1);
  assert.throws(() => check({ ...defaultDocument(), duration: 11 }), /duration/);
  assert.throws(() => check({ ...defaultDocument(), params: { F1: [[0], [1, 2]] } }), /F1/);
  assert.throws(() => check({ hello: 1 }), /TrackDraw/);
});

test("a drawing goes into a link and comes back unchanged", () => {
  const doc = defaultDocument();
  const encoded = encodeState(doc);
  assert.match(encoded, /^[A-Za-z0-9_-]+$/);
  assert.deepEqual(decodeState(encoded), doc);
  assert.deepEqual(stateFromHash(`#state=${encoded}`), doc);
  assert.equal(stateFromHash("#nothing"), null);
  // The default drawing is a few hundred bytes, as app.md D8 estimated.
  assert.ok(encoded.length < 600, `link state is ${encoded.length} characters`);
});

test("history undoes and redoes, and a new edit drops the redo branch", () => {
  const history = new History("a");
  history.push("b");
  history.push("c");
  assert.ok(history.undo());
  assert.equal(history.present, "b");
  assert.ok(history.redo());
  assert.equal(history.present, "c");
  history.undo();
  history.push("d");
  assert.equal(history.redo(), false);
  assert.equal(history.present, "d");
});

// sonore refuses a track whose times do not strictly increase ("F0's times
// must increase"), so no edit may leave two breakpoints at one time.
const increasing = (times) => times.every((t, i) => i === 0 || t > times[i - 1]);

test("a point dragged onto its neighbour stays just beside it", () => {
  const doc = defaultDocument();
  const pts = points(doc, "F0");
  const next = withPoints(doc, "F0", movePoint(pts, 1, -1, 110));
  assert.ok(increasing(next.params.F0[0]));
  assert.equal(next.params.F0[0].length, 2);
});

test("a line with no width in time keeps one breakpoint there, the newest", () => {
  const doc = defaultDocument();
  const next = withPoints(doc, "F0", replaceSpan(points(doc, "F0"), [[0.3, 100], [0.30001, 140]]));
  assert.deepEqual(next.params.F0, [[0, 0.3, 0.6], [125, 140, 95]]);
});

test("shrinking the duration never merges times into a repeat", () => {
  const doc = withPoints(defaultDocument(), "F1", [[0, 500], [0.0002, 600], [0.0004, 700], [0.6, 500]]);
  const short = stretch(doc, 0.05);
  for (const value of Object.values(short.params)) if (typeof value !== "number") assert.ok(increasing(value[0]));
});

test("a document from a file or link with repeated times is tidied", () => {
  const doc = { ...defaultDocument(), params: { F0: [[0, 0.3, 0.3, 0.6], [125, 100, 140, 95]] } };
  assert.deepEqual(tidyDocument(doc).params.F0, [[0, 0.3, 0.6], [125, 140, 95]]);
});

test("F0 is never drawn or read below 20 Hz; other tracks still reach 0", () => {
  assert.equal(clampValue("F0", 5), 20);
  assert.equal(clampValue("F0", 120), 120);
  assert.equal(clampValue("F1", -5), 0);
  const doc = { ...defaultDocument(), params: { F0: [[0, 0.3, 0.6], [125, 8, 95]], AV: 0 } };
  assert.deepEqual(tidyDocument(doc).params, { F0: [[0, 0.3, 0.6], [125, 20, 95]], AV: 0 });
  assert.equal(tidyDocument({ ...doc, params: { F0: 10 } }).params.F0, 20);
});
