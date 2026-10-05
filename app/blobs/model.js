// The Modulation tab's state, the plane it is drawn on, and the picture of
// the drawing (docs/design/tabs/blobs.md; sonore_sketch.blobs is the Python
// half).
//
// A blob is sonore's ModulationBlob: a Gaussian bump of power centred on a
// rate [Hz, signed: positive sweeps down, negative up] and a density
// [cycles/octave], with a standard deviation in octaves of rate and one in
// cycles/octave, and a peak level [dB] relative to the other blobs.
//
// No DOM here, so this file runs under `node --test`.

export const FORMAT = 1;
export const CARRIERS = ["tones", "noise"];
export const MAX_BLOBS = 8;
export const ENV_FS = 1000; // sonore's envelope rate for from_blobs

export const DEFAULTS = {
  f_lo: 100, f_hi: 6400, bands_per_octave: 12,
  carrier: "tones", iterations: 0, rms_depth: 0.2, seed: 1,
};
// A new blob's widths and level (B2).
export const NEW_BLOB = { rate_width: 0.5, density_width: 0.25, level: 0 };
// sonore_sketch.blobs.EXAMPLE_ITEMS (B9); tests/test_blobs.py checks the two agree.
export const EXAMPLE_ITEMS = [
  { rate: 4, density: 0, rate_width: 0.5, density_width: 0.25, level: 0 },
  { rate: 8, density: 1, rate_width: 0.5, density_width: 0.25, level: -3 },
];

// The plane shown (B1): rate on a signed log axis from 1 to 64 Hz each side,
// density linear from 0 to 6 cycles/octave.
export const RATE_MIN = 1;
export const RATE_MAX = 64;
export const DENSITY_MAX = 6;
export const WIDTH_MIN = 0.05;
export const WIDTH_MAX = 3;
export const COARSE_BELOW_S = 2; // B8: a note on this tab below this duration

export function defaultSection() {
  return { ...DEFAULTS, items: EXAMPLE_ITEMS.map((item) => ({ ...item })) };
}

// --- the grid the drawing is heard on --------------------------------------------

// The rates and densities sonore's from_blobs puts the drawing on (and the
// result's analysis measures): rate steps of 1/duration Hz (the envelopes'
// length at 1000 Hz), and density steps of 1 / (bands x octaves per band),
// from 0 up to half the bands' rate.
export function grid({ duration, f_lo, f_hi, bands_per_octave }) {
  const nTimes = Math.round(duration * ENV_FS);
  const nBands = Math.round(Math.log2(f_hi / f_lo) * bands_per_octave) - 1; // the filterbank's bands, less its two edges
  const densityStep = bands_per_octave / nBands;
  const nDensities = Math.ceil(nBands / 2);
  return { rateStep: ENV_FS / nTimes, nTimes, densityStep, densities: Array.from({ length: nDensities }, (_, j) => j * densityStep) };
}

// One blob's power at (rate, density), zero on the other side of the rate
// axis (ModulationBlob.power).
export function blobPower({ rate, density, rate_width, density_width, level }, r, d) {
  if (Math.sign(r) !== Math.sign(rate)) return 0;
  const octaves = Math.log2(Math.abs(r) / Math.abs(rate));
  return 10 ** (level / 10) * Math.exp(-(octaves ** 2) / (2 * rate_width ** 2) - (d - density) ** 2 / (2 * density_width ** 2));
}

// The drawing's power at (rate, density): the blobs' sum, made the same at
// (-rate, -density), as from_blobs does, since a real envelope's spectrum is.
export function power(items, r, d) {
  let total = 0;
  for (const blob of items) total += blobPower(blob, r, d) + blobPower(blob, -r, -d);
  return total / 2;
}

// --- the plane's rate axis ---------------------------------------------------------

// Where a rate sits on the signed log axis, from -1 (-RATE_MAX) through the
// seam at 0 (±RATE_MIN) to 1 (RATE_MAX). Rates nearer 0 than RATE_MIN sit
// on the seam.
export function rateToUnit(rate) {
  const span = Math.log2(RATE_MAX / RATE_MIN);
  const u = Math.min(1, Math.max(0, Math.log2(Math.max(Math.abs(rate), RATE_MIN) / RATE_MIN) / span));
  return rate < 0 ? -u : u;
}

// The rate at a place on the axis (the inverse of rateToUnit); 0 is taken
// as the positive side's RATE_MIN.
export function unitToRate(u) {
  const magnitude = RATE_MIN * 2 ** (Math.min(1, Math.abs(u)) * Math.log2(RATE_MAX / RATE_MIN));
  return u < 0 ? -magnitude : magnitude;
}

// A blob's rate kept on the plane: 1 to 64 Hz in size, on its own side.
export function clampRate(rate) {
  const magnitude = Math.min(RATE_MAX, Math.max(RATE_MIN, Math.abs(rate)));
  return rate < 0 ? -magnitude : magnitude;
}

export function clampDensity(density) {
  return Math.min(DENSITY_MAX, Math.max(0, density));
}

export function clampWidth(width) {
  return Math.min(WIDTH_MAX, Math.max(WIDTH_MIN, width));
}

// Numbers as saved: two decimals are finer than any blob's width.
export const tidy = (x) => Math.round(x * 100) / 100;

// --- sonore's refusals -----------------------------------------------------------

// The depth sonore says fits, from its refusal of a deeper one
// ("... at most 0.342 fits it ..."), or null.
export function depthThatFits(message) {
  const match = /at most ([0-9]*\.?[0-9]+) fits/.exec(message ?? "");
  return match ? Number(match[1]) : null;
}

// --- checking --------------------------------------------------------------------

const ITEM_KEYS = ["rate", "density", "rate_width", "density_width", "level"];

// Raise an Error saying what is wrong with a section from a file or a link;
// sonore_sketch.blobs.check does the same in Python (with the page's fs).
export function check(state) {
  const { f_lo, f_hi, bands_per_octave, carrier, iterations, rms_depth, seed, items } = state;
  if (!(f_lo > 0 && f_hi > f_lo)) throw new Error("the modulation tab's frequency range must have 0 < f_lo < f_hi");
  if (!(Number.isInteger(bands_per_octave) && bands_per_octave >= 1)) throw new Error("bands_per_octave must be a whole number of at least 1");
  if (!CARRIERS.includes(carrier)) throw new Error(`the modulation carrier must be one of ${CARRIERS.join(", ")}`);
  if (!(Number.isInteger(iterations) && iterations >= 0 && iterations <= 10)) throw new Error("iterations must be a whole number from 0 to 10");
  if (!(rms_depth > 0 && rms_depth <= 1)) throw new Error("rms_depth must be in (0, 1]");
  if (!Number.isInteger(seed)) throw new Error("seed must be a whole number");
  if (!Array.isArray(items) || items.length > MAX_BLOBS) throw new Error(`items must be a list of at most ${MAX_BLOBS} blobs`);
  items.forEach((item, i) => {
    if (!ITEM_KEYS.every((key) => Number.isFinite(item?.[key]))) throw new Error(`blob ${i + 1} must give a number for each of ${ITEM_KEYS.join(", ")}`);
    if (item.rate === 0 || item.rate_width <= 0 || item.density_width <= 0) throw new Error(`blob ${i + 1} needs a nonzero rate and positive widths`);
  });
  return state;
}
