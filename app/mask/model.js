// The Filter recording tab's state and its mask
// (docs/design/tabs/mask.md; sonore_sketch.mask is the Python half).
//
// The mask is a grid of cuts in dB, one byte a cell, stored as the other
// tabs store theirs (base64 of deflated bytes, rows from 0 Hz up): 0 keeps a
// cell, -floor_db (60) removes it. Its rows are equal steps of frequency
// from 0 Hz to Nyquist (F4) and its columns equal fractions of the
// duration, so it stretches with the duration. The source is the Edit
// modulation tab's (F2), and so is the page's recording.
//
// No DOM here, so this file runs under `node --test`.

import { SOURCES } from "../edit/model.js";

export { SOURCES };
export const FORMAT = 1;
export const ROWS = 256;
export const COLUMNS = 256;
export const FLOOR_DB = -60;
export const WINDOW_S = 0.032; // F5

// sonore_sketch.mask.BLANK_LEVELS: nothing cut, so the first Play is the
// source; tests/js/mask.test.mjs checks the two agree.
export const BLANK_LEVELS = "eNrtwQEBAAAAgJD+r+4ICgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGoADwAB";

export const DEFAULTS = { source: "syllables", rows: ROWS, columns: COLUMNS, floor_db: FLOOR_DB, window: WINDOW_S };

export function defaultSection() {
  return { ...DEFAULTS, levels: BLANK_LEVELS };
}

export function blank() {
  return new Uint8Array(ROWS * COLUMNS);
}

export function isBlank(bytes) {
  return bytes.every((b) => b === 0);
}

// A row's centre frequency [Hz] at sampling rate fs.
export const rowFrequency = (r, fs) => ((r + 0.5) / ROWS) * (fs / 2);

// Raise an Error saying what is wrong with a section from a file or a link
// (the mask itself is checked when decoded); sonore_sketch.mask.check does
// the same in Python.
export function check(state) {
  const { source, rows, columns, floor_db, window, levels } = state;
  if (!SOURCES.includes(source)) throw new Error(`the filter source must be one of ${SOURCES.join(", ")}`);
  if (rows !== ROWS || columns !== COLUMNS || floor_db !== FLOOR_DB || window !== WINDOW_S) {
    throw new Error(`the filter mask must be ${ROWS} rows x ${COLUMNS} columns with a floor of ${FLOOR_DB} dB and a ${WINDOW_S} s window`);
  }
  if (typeof levels !== "string") throw new Error("the filter mask's levels must be text");
  return state;
}
