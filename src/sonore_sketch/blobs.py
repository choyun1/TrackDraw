"""The Modulation tab's state, and the sound it describes.

A drawing is a list of Gaussian blobs on a modulation spectrum, rate [Hz,
signed] by density [cycles/octave] (docs/design/tabs/blobs.md)::

    {"blobs": 1, "sonore": "0.5.0", "duration": 3.0, "fs": 16000,
     "f_lo": 100, "f_hi": 6400, "bands_per_octave": 12,
     "carrier": "tones", "f0": 100, "iterations": 0, "rms_depth": 0.2, "seed": 1,
     "items": [{"rate": 4, "density": 0, "rate_width": 0.5,
                "density_width": 0.25, "level": 0}, ...],
     "bands": [{"points": [[0, 500], [3, 500]], "width": 1, "level": 0}, ...]}

Each item is a ``so.ModulationBlob``; the sound is
``so.ModulationSpectrum.from_blobs(...).to_sound(...)``, RMS 1. The seed
draws the modulation phase (and the noise carrier), so a drawing always
gives the same samples. The harmonic carrier is a harmonic complex on
``f0`` whose band-by-band fine structure carries the drawn envelopes, as
``to_sound`` does for a recording but with the modulation phase drawn from
the seed.

``bands`` (optional, docs/design/tabs/bands.md) confine the sound to drawn
regions of the spectrogram: each is a centre-frequency track, a width in
octaves and a level, applied last as a time-varying filter on a 20 ms STFT
(``so.Mask``). With no bands the sound is the whole range, as before.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import sonore as so

FORMAT = 1
MAX_DURATION = 10.0  # seconds, the whole app's limit (docs/design/app.md, D10)
CARRIERS = ("tones", "harmonic", "noise")  # blobs.md, B3, and Cho's harmonic complex
MAX_BLOBS = 8  # B2
MAX_ITERATIONS = 10  # B4
ITEM_KEYS = ("rate", "density", "rate_width", "density_width", "level")
MAX_BANDS = 5  # bands.md
BAND_WIDTHS = (1 / 6, 4.0)  # octaves, K3
BAND_LEVELS = (-40.0, 0.0)  # dB, K4
BAND_SKIRT = 1 / 6  # octaves of raised-cosine edge on each side (K2)
BAND_FLOOR_DB = -60.0  # what lies outside every band (K2)
BAND_WINDOW_S = 0.02  # the STFT the bands are applied on (K1)


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check(state: Mapping[str, Any]) -> None:
    """Raise ``ValueError`` saying what is wrong with ``state``, if anything."""
    if state.get("blobs") != FORMAT:
        raise ValueError(f"not a Modulation state of format {FORMAT}: 'blobs' is {state.get('blobs')!r}")
    duration, fs = state.get("duration"), state.get("fs")
    if not _number(duration) or not 0 < duration <= MAX_DURATION:
        raise ValueError(f"'duration' must be a number of seconds in (0, {MAX_DURATION:g}], not {duration!r}")
    if not _number(fs) or fs <= 0:
        raise ValueError(f"'fs' must be a positive sampling rate, not {fs!r}")
    f_lo, f_hi = state.get("f_lo"), state.get("f_hi")
    if not (_number(f_lo) and _number(f_hi) and 0 < f_lo < f_hi < fs / 2):
        raise ValueError(f"the frequency range must have 0 < f_lo < f_hi < fs/2 = {fs / 2:g} Hz, not {f_lo!r}-{f_hi!r}")
    if not (isinstance(state.get("bands_per_octave"), int) and state["bands_per_octave"] >= 1):
        raise ValueError("'bands_per_octave' must be a whole number of at least 1")
    if state.get("carrier", "tones") not in CARRIERS:
        raise ValueError(f"'carrier' must be one of {CARRIERS}, not {state.get('carrier')!r}")
    f0 = state.get("f0", 100)
    if state.get("carrier") == "harmonic" and not (_number(f0) and 20 <= f0 <= f_hi):
        raise ValueError(f"'f0' must be a frequency from 20 Hz up to f_hi for the harmonic carrier, not {f0!r}")
    iterations = state.get("iterations", 0)
    if not (isinstance(iterations, int) and 0 <= iterations <= MAX_ITERATIONS):
        raise ValueError(f"'iterations' must be a whole number from 0 to {MAX_ITERATIONS}, not {iterations!r}")
    depth = state.get("rms_depth", 0.2)
    if not (_number(depth) and 0 < depth <= 1):
        raise ValueError(f"'rms_depth' must be a number in (0, 1], not {depth!r}")
    items = state.get("items")
    if not isinstance(items, list) or len(items) > MAX_BLOBS:
        raise ValueError(f"'items' must be a list of at most {MAX_BLOBS} blobs")
    for i, item in enumerate(items):
        if not isinstance(item, Mapping) or not all(_number(item.get(key)) for key in ITEM_KEYS):
            raise ValueError(f"blob {i + 1} must give a number for each of {', '.join(ITEM_KEYS)}")
        if item["rate"] == 0 or item["rate_width"] <= 0 or item["density_width"] <= 0:
            raise ValueError(f"blob {i + 1} needs a nonzero rate and positive widths")
    bands = state.get("bands", [])
    if not isinstance(bands, list) or len(bands) > MAX_BANDS:
        raise ValueError(f"'bands' must be a list of at most {MAX_BANDS} bands")
    for i, band in enumerate(bands):
        _check_band(band, i, duration, f_lo, f_hi)


def _check_band(band: Any, i: int, duration: float, f_lo: float, f_hi: float) -> None:
    name = f"band {i + 1}"
    if not isinstance(band, Mapping):
        raise ValueError(f"{name} must be an object with points, width and level")
    width, level = band.get("width"), band.get("level", 0)
    if not (_number(width) and BAND_WIDTHS[0] - 1e-9 <= width <= BAND_WIDTHS[1]):
        raise ValueError(f"{name}'s width must be from 1/6 to {BAND_WIDTHS[1]:g} octaves, not {width!r}")
    if not (_number(level) and BAND_LEVELS[0] <= level <= BAND_LEVELS[1]):
        raise ValueError(f"{name}'s level must be from {BAND_LEVELS[0]:g} to {BAND_LEVELS[1]:g} dB, not {level!r}")
    points = band.get("points")
    if not (isinstance(points, list) and points and all(isinstance(p, (list, tuple)) and len(p) == 2 and all(_number(v) for v in p) for p in points)):
        raise ValueError(f"{name} needs a list of [time, Hz] points")
    times = [p[0] for p in points]
    if any(b <= a for a, b in zip(times, times[1:])) or times[0] < 0 or times[-1] > duration + 1e-9:
        raise ValueError(f"{name}'s times must increase, within 0 to {duration:g} s")
    if any(not f_lo <= p[1] <= f_hi for p in points):
        raise ValueError(f"{name}'s centre must stay within {f_lo:g}-{f_hi:g} Hz")


def band_centres(points: list, t: np.ndarray) -> np.ndarray:
    """A band's centre [Hz] at times ``t``: its points interpolated in log
    frequency, held past the first and the last."""
    times = np.array([p[0] for p in points], float)
    hz = np.array([p[1] for p in points], float)
    return 2 ** np.interp(t, times, np.log2(hz))


def band_gain(bands: list, freqs: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Amplitude gain of ``bands`` at times ``t`` and frequencies ``freqs``,
    shape ``(len(t), len(freqs))``: 1 times a band's level within half its
    width of its centre, a raised-cosine skirt of ``BAND_SKIRT`` octaves,
    ``BAND_FLOOR_DB`` outside, and the largest over the bands (K2, K5)."""
    floor = 10 ** (BAND_FLOOR_DB / 20)
    octaves = np.log2(np.maximum(np.asarray(freqs, float), 1e-3))[None, :]
    gain = np.full((len(t), octaves.shape[1]), floor)
    for band in bands:
        centre = np.log2(band_centres(band["points"], np.asarray(t, float)))[:, None]
        edge = np.clip((np.abs(octaves - centre) - band["width"] / 2) / BAND_SKIRT, 0, 1)
        peak = 10 ** (band.get("level", 0) / 20)
        gain = np.maximum(gain, floor + (peak - floor) * 0.5 * (1 + np.cos(np.pi * edge)))
    return gain


def band_limit(sound: so.Sound, bands: list) -> so.Sound:
    """``sound`` through the bands' time-varying filter, RMS 1 (K1)."""
    stft = so.STFT(sound, BAND_WINDOW_S)
    gain = band_gain(bands, stft.f, np.clip(stft.t, 0, sound.duration))
    out = (stft * so.Mask(gain.T[None, :, :], stft)).to_sound()
    out = so.Sound(out.mono().data[: sound.n_samples], sound.fs)
    return out.normalize() if out.rms > 0 else out


def blobs(state: Mapping[str, Any]) -> list[so.ModulationBlob]:
    """The drawing as sonore's blobs."""
    return [so.ModulationBlob(*(float(item[key]) for key in ITEM_KEYS)) for item in state["items"]]


def target(state: Mapping[str, Any]) -> so.ModulationSpectrum:
    """The drawn modulation spectrum, on the grid the sound's own analysis
    would have (``ModulationSpectrum.from_blobs``)."""
    return so.ModulationSpectrum.from_blobs(
        blobs(state),
        float(state["duration"]),
        f_lo=float(state["f_lo"]),
        f_hi=float(state["f_hi"]),
        bands_per_octave=int(state["bands_per_octave"]),
        rms_depth=float(state.get("rms_depth", 0.2)),
    )


def synthesize(state: Mapping[str, Any]) -> so.Sound:
    """The sound ``state`` describes. A depth one draw cannot reach is
    sonore's ``ValueError``, which names the depth that fits."""
    check(state)
    if not state["items"]:
        raise ValueError("no blobs yet: add a blob to hear something")
    if state.get("carrier") == "harmonic":
        sound = _on_harmonics(state)
    else:
        sound = target(state).to_sound(
            carrier=state.get("carrier", "tones"),
            fs=float(state["fs"]),
            rng=int(state.get("seed", 1)),
            iterations=int(state.get("iterations", 0)),
        )
    return band_limit(sound, state["bands"]) if state.get("bands") else sound


def _on_harmonics(state: Mapping[str, Any]) -> so.Sound:
    """The drawing's envelopes, drawn with the seed, on the fine structure of
    a harmonic complex in each band: ``to_sound``'s route for a recording
    carrier, which would otherwise take the modulation phase from the
    (unmodulated) complex itself."""
    if state.get("iterations", 0):
        raise ValueError("iterations work on the tones and noise carriers only")
    fs, duration = float(state["fs"]), float(state["duration"])
    envelopes = target(state).to_envelopes(rng=int(state.get("seed", 1)))
    complex_tone = so.harmonic_complex(duration, fs, float(state.get("f0", 100)))
    fine = envelopes.filterbank.analyze(complex_tone).tfs()
    sound = (envelopes * fine).to_sound()
    sound = so.Sound(sound.data[: complex_tone.data.shape[0]], fs)
    return sound.normalize()


# The measured result under the plane (blobs.md, B7): the plane's own range.
MEASURED_RATE_MAX = 64.0  # Hz, each side
MEASURED_DENSITY_MAX = 6.0  # cycles/octave
MEASURED_FLOOR_DB = -40.0  # the picture's range below its peak, as the plane's
ENV_FS = 1000.0  # sonore's envelope rate for octave() and from_blobs


def measured(sound: so.Sound, state: Mapping[str, Any]) -> so.ModulationSpectrum:
    """The modulation spectrum of ``sound``, analysed as ``octave`` does
    (1/``bands_per_octave``-octave cosine filterbank over the tab's range,
    envelopes at 1 kHz).

    With bands, within the bands, following them (bands.md, K7): each band's
    envelope is divided by the gain the bands gave it, taken relative to its
    mean, and weighted by that gain before the transform. The bands' own
    shape and motion (their gain) then drop out, and what is measured is the
    modulation inside them, which is what the blobs draw; the weighting blurs
    it by the bands' extent, as any window does."""
    bank = so.cosine_filterbank(
        f_lo=float(state["f_lo"]), f_hi=float(state["f_hi"]), spacing=1 / int(state["bands_per_octave"]), scale="octave"
    )
    env = bank.analyze(sound.mono()).envelopes(fs=ENV_FS).data.mean(axis=2)[:, 1:-1]  # (time, band), edges dropped
    if state.get("bands"):
        t = np.arange(env.shape[0]) / ENV_FS
        gain = band_gain(state["bands"], bank.cfs[1:-1], t)
        weight = gain / gain.max()
        relative = env / np.maximum(gain, 10 ** (BAND_FLOOR_DB / 20))
        mean = np.sum(weight * relative) / np.sum(weight)
        env = weight * (relative / mean - 1)
    return so.ModulationSpectrum.from_array(env.T, dt=1 / ENV_FS, dx=bank.spacing, spectral_unit=f"cyc/{bank.unit}")


def measured_picture(spectrum: so.ModulationSpectrum) -> dict[str, Any]:
    """The measured spectrum on the plane's range as 8-bit levels, 0 at
    ``MEASURED_FLOOR_DB`` below the peak and 255 at it, the peak taken away
    from rate 0 (the long-term spectrum, which the plane does not show).
    Rows are densities from 0 up, columns rates from the most negative."""
    rates = np.abs(spectrum.w_t) <= MEASURED_RATE_MAX
    densities = spectrum.w_f <= MEASURED_DENSITY_MAX + 1e-9
    level = spectrum.level[np.ix_(densities, rates)]
    w_t = spectrum.w_t[rates]
    peak = level[:, np.abs(w_t) > 0].max()
    scaled = np.round(255 * (1 - np.clip(level - peak, MEASURED_FLOOR_DB, 0) / MEASURED_FLOOR_DB))
    return {
        "data": np.ascontiguousarray(scaled, dtype=np.uint8).tobytes(),
        "n_densities": int(level.shape[0]),
        "n_rates": int(level.shape[1]),
        "rate_first": float(w_t[0]),
        "rate_step": float(w_t[1] - w_t[0]),
        "density_step": float(spectrum.w_f[1]),
        "floor_db": MEASURED_FLOOR_DB,
    }


# The drawing the tab starts from (B9): a syllable-rate flutter, and ripples
# sweeping down at twice the rate, 3 dB weaker.
EXAMPLE_ITEMS = [
    {"rate": 4.0, "density": 0.0, "rate_width": 0.5, "density_width": 0.25, "level": 0.0},
    {"rate": 8.0, "density": 1.0, "rate_width": 0.5, "density_width": 0.25, "level": -3.0},
]
