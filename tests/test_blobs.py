import json
import re
from pathlib import Path

import numpy as np
import pytest
import sonore as so

from sonore_sketch import blobs, page

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "blob_power.json"


def state(**changes):
    return {
        "blobs": 1, "sonore": "0.5.0", "duration": 1.0, "fs": 16000,
        "f_lo": 100, "f_hi": 6400, "bands_per_octave": 12,
        "carrier": "tones", "iterations": 0, "rms_depth": 0.2, "seed": 1,
        "items": [dict(item) for item in blobs.EXAMPLE_ITEMS],
    } | changes


def picture_fixture():
    """What the page's picture must agree with (tests/js/blobs.test.mjs):
    from_blobs's grid, and its level at some cells, in dB below its peak."""
    drawing = state(items=[*blobs.EXAMPLE_ITEMS, {"rate": -6, "density": 2, "rate_width": 0.3, "density_width": 0.5, "level": -6}])
    spectrum = blobs.target(drawing)
    level = spectrum.level - spectrum.level.max()
    points = []
    for j in range(0, 18, 1):
        for i in np.flatnonzero((np.abs(spectrum.w_t) >= 1) & (np.abs(spectrum.w_t) <= 20)):
            if level[j, i] > -40:
                points.append([round(float(spectrum.w_t[i]), 6), round(float(spectrum.w_f[j]), 6), round(float(level[j, i]), 4)])
    return {
        "state": {k: drawing[k] for k in ("duration", "f_lo", "f_hi", "bands_per_octave", "items")},
        "rate_step": float(spectrum.w_t[1] - spectrum.w_t[0]),
        "n_rates": len(spectrum.w_t),
        "density_step": float(spectrum.w_f[1]),
        "n_densities": len(spectrum.w_f),
        "points": points,
    }


def test_the_pages_picture_fixture_is_what_sonore_draws():
    # Regenerate with: python tests/test_blobs.py
    saved, now = json.loads(FIXTURE.read_text()), json.loads(json.dumps(picture_fixture()))
    assert saved["state"] == now["state"] and saved["n_rates"] == now["n_rates"] and saved["n_densities"] == now["n_densities"]
    assert saved["rate_step"] == pytest.approx(now["rate_step"]) and saved["density_step"] == pytest.approx(now["density_step"])
    assert np.array(saved["points"]) == pytest.approx(np.array(now["points"]), abs=1e-3)


def test_the_page_starts_from_the_same_example():
    model = (ROOT / "app" / "blobs" / "model.js").read_text()
    block = re.search(r"EXAMPLE_ITEMS = \[(.*?)\];", model, re.S).group(1)
    items = [{k: float(v) for k, v in re.findall(r"(\w+): (-?[0-9.]+)", entry)} for entry in re.findall(r"\{([^}]*)\}", block)]
    assert items == blobs.EXAMPLE_ITEMS


@pytest.mark.parametrize("carrier", ["tones", "harmonic"])
def test_a_blob_is_heard_where_it_is_drawn(carrier):
    # blobs.md, B-M2, as a test: at 3 s, the result's measured modulation
    # peaks within the blob's width of where it was drawn.
    sound = blobs.synthesize(state(duration=3.0, carrier=carrier, items=[{"rate": 8, "density": 1, "rate_width": 0.3, "density_width": 0.25, "level": 0}]))
    measured = so.ModulationSpectrum.octave(sound, f_lo=100, f_hi=6400)
    # Rate 0 is left out: no blob can be there, and a harmonic complex's own
    # static spectral ripple (its harmonics) is.
    rates = (np.abs(measured.w_t) <= 40) & (np.abs(measured.w_t) >= 1)
    near = rates[None, :] & (measured.w_f <= 4)[:, None]
    j, i = np.unravel_index(np.argmax(np.where(near, measured.level, -np.inf)), measured.level.shape)
    assert 8 * 2**-0.6 <= measured.w_t[i] <= 8 * 2**0.6 and abs(measured.w_f[j] - 1) <= 0.5


def test_the_harmonic_carrier_is_a_harmonic_complex_on_f0():
    data = blobs.synthesize(state(carrier="harmonic", f0=125)).mono().data[:, 0]
    spectrum = np.abs(np.fft.rfft(data * np.hanning(len(data)))) ** 2
    f = np.fft.rfftfreq(len(data), 1 / 16000)
    on = np.isin(np.round(f), 125 * np.arange(1, 52))  # 1 Hz bins: the harmonics' own
    assert spectrum[on].sum() / spectrum.sum() > 0.5  # mostly at harmonics, though the envelopes widen each


def test_iterations_are_refused_on_the_harmonic_carrier():
    with pytest.raises(ValueError, match="iterations"):
        blobs.synthesize(state(carrier="harmonic", iterations=2))


@pytest.mark.parametrize("carrier", blobs.CARRIERS)
def test_every_carrier_gives_the_same_samples_twice(carrier):
    a = blobs.synthesize(state(carrier=carrier))
    b = blobs.synthesize(state(carrier=carrier))
    assert a.duration == pytest.approx(1.0) and np.array_equal(a.data, b.data)
    assert np.sqrt(np.mean(a.data**2)) == pytest.approx(1)
    assert not np.array_equal(a.data, blobs.synthesize(state(carrier=carrier, seed=2)).data)


def test_too_deep_a_drawing_is_refused_with_the_depth_that_fits():
    with pytest.raises(ValueError, match=r"at most 0\.[0-9]+ fits"):
        blobs.synthesize(state(rms_depth=0.95))


def test_no_blobs_says_so():
    with pytest.raises(ValueError, match="no blobs yet"):
        blobs.synthesize(state(items=[]))


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"blobs": 2}, "format 1"),
        ({"f_hi": 8000}, "fs/2"),
        ({"carrier": "pink"}, "carrier"),
        ({"carrier": "harmonic", "f0": 5}, "f0"),
        ({"carrier": "harmonic", "iterations": 2, "items": []}, None),
        ({"iterations": 11}, "iterations"),
        ({"rms_depth": 0}, "rms_depth"),
        ({"items": [{"rate": 0, "density": 0, "rate_width": 0.5, "density_width": 0.25, "level": 0}]}, "nonzero rate"),
        ({"items": [{"rate": 4}]}, "a number for each"),
        ({"items": [dict(blobs.EXAMPLE_ITEMS[0])] * 9}, "at most 8"),
    ],
)
def test_bad_states_are_refused(changes, message):
    if message is None:  # allowed by check
        return blobs.check(state(**changes))
    with pytest.raises(ValueError, match=message):
        blobs.check(state(**changes))


def test_a_saved_page_on_the_modulation_tab_sounds_as_the_tab_does():
    section = {k: v for k, v in state().items() if k not in ("blobs", "sonore", "duration", "fs")}
    document = {
        "app": "sonore-sketch", "version": 2, "sonore": "0.5.0", "duration": 1.0, "fs": 16000,
        "tab": "blobs", "tracks": {"mode": "klatt", "params": {}}, "blobs": section,
    }
    assert np.array_equal(page.synthesize(document).data, blobs.synthesize(state()).data)


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(picture_fixture(), indent=0) + "\n")
    print(f"wrote {FIXTURE.relative_to(ROOT)}")
