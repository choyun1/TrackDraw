"""The Modulation tab's state, and the sound it describes.

A drawing is a list of Gaussian blobs on a modulation spectrum, rate [Hz,
signed] by density [cycles/octave] (docs/design/tabs/blobs.md)::

    {"blobs": 1, "sonore": "0.5.0", "duration": 3.0, "fs": 16000,
     "f_lo": 100, "f_hi": 6400, "bands_per_octave": 12,
     "carrier": "tones", "iterations": 0, "rms_depth": 0.2, "seed": 1,
     "items": [{"rate": 4, "density": 0, "rate_width": 0.5,
                "density_width": 0.25, "level": 0}, ...]}

Each item is a ``so.ModulationBlob``; the sound is
``so.ModulationSpectrum.from_blobs(...).to_sound(...)``, RMS 1. The seed
draws the modulation phase (and the noise carrier), so a drawing always
gives the same samples.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import sonore as so

FORMAT = 1
MAX_DURATION = 10.0  # seconds, the whole app's limit (docs/design/app.md, D10)
CARRIERS = ("tones", "noise")  # blobs.md, B3
MAX_BLOBS = 8  # B2
MAX_ITERATIONS = 10  # B4
ITEM_KEYS = ("rate", "density", "rate_width", "density_width", "level")


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
    return target(state).to_sound(
        carrier=state.get("carrier", "tones"),
        fs=float(state["fs"]),
        rng=int(state.get("seed", 1)),
        iterations=int(state.get("iterations", 0)),
    )


# The drawing the tab starts from (B9): a syllable-rate flutter, and ripples
# sweeping down at twice the rate, 3 dB weaker.
EXAMPLE_ITEMS = [
    {"rate": 4.0, "density": 0.0, "rate_width": 0.5, "density_width": 0.25, "level": 0.0},
    {"rate": 8.0, "density": 1.0, "rate_width": 0.5, "density_width": 0.25, "level": -3.0},
]
