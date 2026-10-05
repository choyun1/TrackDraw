# Bands on the Modulation tab: band-limiting the blobs

An addition to the Modulation tab (`blobs.md`). Today the carrier fills
every band from 100 to 6400 Hz, so wherever a blob sits on the plane, the
sound covers the whole spectrogram. Cho asked (2026-10-05) for a way to
band-limit it, perhaps as drawn tracks: a time-varying filter like a
formant, with up to about five bands. This note designs that.

Status: proposed (2026-10-05), waiting on Cho's answers to K1–K7. Nothing
is built yet beyond `tools/measure_bands.py`.

This project is AI-assisted: the document and `tools/measure_bands.py`
were drafted by Claude (Claude Code), for Cho to review.

## Why

A modulation spectrum says how the envelopes move, not where in frequency
they are. Real sounds put their modulation in places: a vowel's syllable
rhythm rides on its formants, a bird's trill sits in one octave. With
bands, a drawing can say both: "4 Hz flutter, but only around 500 Hz and
2 kHz, and the upper band rising". It also makes the lessons sharper: a
blob at 1 cyc/oct heard in a 2-octave band is two ripples sweeping
through a window, not a sheet across the whole range.

## How the claims are verified

As in `blobs.md`: **[measure]** is printed by `tools/measure_bands.py`
(sonore 0.5.0 natively, 16 kHz, 100–6400 Hz, 12 bands per octave, the two
starting blobs, rng 1, on a 4-core Linux cloud container, so not an
independent check); **[read]** is read from sonore's source;
**[estimate]** gives its basis.

## What a band is

A **band** is a centre-frequency track (breakpoints in time, as on the
Speech tab, interpolated in log frequency and held past the ends), a
width in octaves and a level in dB. Its gain is 1 (times its level)
within half the width of the centre, falls along a raised-cosine skirt of
1/6 octave on each side, and reaches a floor of −60 dB. Several bands
combine by taking the largest gain at each time and frequency. With no
bands the tab sounds as it does now.

## Three ways to put the gain on the sound

- **envelopes**: multiply each carrier band's envelope by the gain at its
  centre, before the fine structure goes under it. Exact, but it means
  writing out `to_sound`'s tones and noise routes in the page's Python
  (`to_sound` takes no gain), and iterations would pull the result back
  toward the unbanded target, since they re-impose the stored magnitudes
  [read: `ModulationSpectrum.to_sound`].
- **subbands**: synthesize as now, analyse the result with the same cosine
  filterbank, multiply by a `so.Mask`, resynthesize.
- **stft**: the same with a 20 ms `so.STFT` and a gain per bin.

The last two are a time-varying filter after synthesis; they work on any
carrier, after iterations, and would work on a recording (the parked
Filter recording tab, `mask.md`) without change. `so.Mask` already does
the multiplying [read: `sonore/views/mask.py`].

## Measurements

**K-M1. All three routes reject about the same: 45–58 dB.** [measure]
Long-term level inside a static band at 1 kHz over the level half an
octave or more outside it, 3 s:

| Band | Carrier | envelopes | subbands | stft |
|---|---|---|---|---|
| 2 oct | tones | 52.7 dB | 54.4 dB | 53.7 dB |
| 2 oct | harmonic | 45.8 dB | 44.9 dB | 44.9 dB |
| 2 oct | noise | 57.8 dB | 57.7 dB | 57.4 dB |
| 1 oct | tones | 53.7 dB | 51.4 dB | 51.2 dB |
| 1/3 oct | tones | 53.5 dB | 54.3 dB | 54.1 dB |

The floor of −60 dB sets the limit; the routes differ by about 2 dB.

**K-M2. Static bands keep the blobs; a moving band adds modulation of its
own.** [measure] The B-M4 contrast of `blobs.md` (measured power where
the drawing is within 6 dB of its peak over where it is 30 dB or more
below), leaving out |rate| < 1 Hz, where a band's own spectral shape
lands; tones, 3 s. "Band only" analyses just the band's own range.

| Case | whole range | band only |
|---|---|---|
| no band | 26.1 dB | |
| 2 oct at 1 kHz | 27.0 dB | 23.6 dB |
| 1 oct at 1 kHz | 24.0 dB | 21.5 dB |
| two 1/2-oct bands, 500 Hz and 2 kHz | 19.8 dB | |
| 1 oct gliding 500 → 4000 Hz (1 oct/s) | 10.0 dB | |

The envelopes and subbands routes give the same numbers to 0.1 dB. A
static band costs a few dB: a narrower band holds fewer carrier bands, so
the density axis is resolved more coarsely (a band *w* octaves wide
resolves density in steps of about 1/*w* cyc/oct [estimate: the width of
the analysis window in octaves]). A glide is a sweep, and a sweep is
modulation at low rate and some density, so the measured plane shows the
glide as well as the blobs. That is what the drawing asks for, not a
fault, but the hint under the plane should say so (K7).

**K-M3. The STFT route is nearly free.** [measure] Tones, one 1-octave
band, warm median of three:

| | 3 s | 10 s |
|---|---|---|
| plain synthesis | 0.24 s | 1.50 s |
| envelopes route (synthesis included) | 0.25 s | 1.62 s |
| subbands route (added to synthesis) | 0.55 s | 1.97 s |
| stft route (added to synthesis) | 0.03 s | 0.09 s |

## Proposed design

### Interface (sketch)

```
┌ plane: rate × density, blobs as now ─────────────────────┬──────────────┐
│                                                          │ Band 2 of 3  │
├──────────────────────────────────────────────────────────┤  width 1 oct │
│ 6400 ┤░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  level 0 dB  │
│      │            ___●________●___                       │  Delete band │
│ 2000 ┤ ●━━━━━━━━━━━              ━━━━━━━━━━● (band 2)     │ Add band     │
│      │                                                   │              │
│  500 ┤ ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━● (band 1)    │              │
│  100 ┤░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │              │
│      └ result's spectrogram, log frequency, bands on top ┘│              │
└──────────────────────────────────────────────────────────┴──────────────┘
```

- The bands are drawn on the spectrogram panel already under the plane
  (time × log frequency, 100–6400 Hz), each as its centre line with
  breakpoint circles and a translucent strip one width wide, so the
  drawing sits on what came out.
- Gestures follow the Speech tab: drag a circle to move it, click on a
  band's line to add a breakpoint, Delete removes the selected
  breakpoint (or the band, with the band selected and no point). "Add
  band" places a flat band, one octave wide, at a free frequency.
- The side panel edits the selected band's width and level. Up to five
  bands.

### Data model

An optional list in the `blobs` section; old links have none and sound as
before, so the section's format number stays 1:

```json
"bands": [
  {"points": [[0, 500], [0.6, 500]], "width": 1, "level": 0},
  {"points": [[0, 2000], [0.3, 2600], [0.6, 2000]], "width": 0.5, "level": -6}
]
```

Times stretch with the page's duration, as the Speech tab's tracks do.

### Python side

`blobs.synthesize` applies the bands last, after the carrier and any
iterations, through `so.STFT` and `so.Mask`, then normalizes to RMS 1 as
now. The gain function and the track interpolation live in `blobs.py`, so no
new module needs adding to the worker's `PYTHON_FILES`. The page draws the strips from the same formula
in JavaScript. Tests: rejection of a static band (K-M1, as a test), no
bands gives today's samples exactly, a saved state gives the same samples
in Python and from the page.

## Decisions

**K1. Where the gain goes.**
(a) a time-varying filter after synthesis, on a 20 ms STFT;
(b) the same on the cosine filterbank's subbands;
(c) on the envelopes before the carrier.
*Recommended:* (a). K-M1 and K-M2 show the three give the same sound to
within about 2 dB; (a) costs almost nothing (K-M3), works with every
carrier and with iterations, and would carry over to recordings. Its
50 Hz bins are coarse only below about 300 Hz, where a 1/3-octave band
spans two or three bins [estimate: bin spacing over band width].

**K2. A band's shape.**
(a) a flat top with 1/6-octave raised-cosine skirts and a −60 dB floor;
(b) a formant resonance (as Klatt's, with its bandwidth in Hz), which
never silences what lies outside;
(c) a Gaussian in log frequency.
*Recommended:* (a), since the ask is to confine the sound: (b) leaves the
whole range audible a few tens of dB down. A formant-like look comes from
the drawing (moving centres, levels), not from the skirts.

**K3. Width.**
(a) one width per band, 1/6 to 4 octaves, default 1;
(b) a width track as well as a centre track.
*Recommended:* (a) for now; (b) doubles the drawing for little gain, and
a band whose width should change can be split into two.

**K4. Level per band.**
(a) a level in dB per band, −40 to 0, constant over time;
(b) none: every band at 0 dB.
*Recommended:* (a): formants differ in strength, and it is one field.

**K5. How bands combine.**
(a) the largest gain; (b) the sum of their powers.
*Recommended:* (a): two overlapping bands then make one wider band
rather than a 3 dB bump where they cross.

**K6. Where they are drawn.**
(a) on the spectrogram panel under the plane, as sketched;
(b) on a panel of their own.
*Recommended:* (a): the drawing lies on its result, and the tab keeps one
time × frequency view.

**K7. What the measured result shows.**
The measured modulation spectrum (blobs.md, B7) stays over the whole
range. With bands drawn, a one-line hint says that moving bands add
modulation of their own (K-M2).
*Recommended:* as stated.

## Order of work

1. Python: the gain, `synthesize` with bands, tests (rejection, no bands
   unchanged).
2. The page: bands on the spectrogram panel, gestures, side panel, the
   page's own gain for the strips, the page check adding a band and
   hearing it. The Edit modulation work in the Handoff doc thread touches
   `app/blobs/`; this step goes after it lands, or is rebased onto it.

## References

- `blobs.md` (the Modulation tab, B-M4, B7), `mask.md` (Filter recording,
  parked).
- sonore: `sonore/views/mask.py` (`Mask`), `sonore/frames/gabor.py`
  (`STFT`), `sonore/views/modulation.py` (`to_sound`).
