# The Filter recording tab: a mask painted on a recording's spectrogram

The third tab of the app (`../app.md`, D7; called "Mask" there): load a
recording, see its spectrogram, paint over parts of it to turn them down or
remove them (a band, a moment, one harmonic), and hear what is left. It
reuses the Paint primitive of `painted.md`, with a cell meaning a gain on the
recording rather than a level of a new sound, and it brings recordings into
the app, which the Edit modulation tab will need too.

Status: proposed, for Cho to decide (2026-10-05). No code until the
decisions below are answered.

This project is AI-assisted: the document and `tools/measure_mask.py` were
drafted by Claude (Claude Code), for Cho to review.

## Why

Erasing part of a spectrogram and hearing the result is the most direct
demonstration of what a spectrogram is, and of its limits: a short-time
Fourier transform cannot be edited freely, because neighbouring
coefficients overlap, so the sound that comes back is the closest sound to
the edited picture, not the picture itself. Showing the result's own
spectrogram under the painting makes that visible, as `../app.md` asks
("drawn target vs what came out").

## How the claims are verified

As in `painted.md`: **[measure]** is printed by `tools/measure_mask.py`,
which runs sonore 0.5.0 natively at 16 kHz on a 4-core Linux cloud
container (not an independent check); **[read]** is read from sonore's
source or docstrings; **[estimate]** gives its basis.

## What sonore provides

- `so.GaborFrame(win_dur, hop_dur).analyze(sound)` gives an `STFT`, and
  `(stft * gains).to_sound()` the least-squares sound for masked
  coefficients [read: `STFT`'s docstring, "the least-squares signal for a
  modified one"]. `gains` may be a plain array of the coefficients' shape
  (frequencies × frames) [measure: run in the script]. Nothing upstream is
  needed.
- `so.load(path)` reads audio files in Python, but in the browser the file
  is decoded by the browser (Web Audio's `decodeAudioData`), which reads
  WAV, MP3, OGG and, in most browsers, M4A, and the samples are sent to
  the worker [estimate: browser support, not tested here].

## Measurements

**F-M1. Speed is no concern.** [measure] Analysis, masking and
resynthesis of noise, hop a quarter window:

| Window | 1 s | 3 s | 10 s |
|---|---|---|---|
| 5 ms (wideband) | 0.041 s | 0.123 s | 0.418 s |
| 32 ms (narrowband) | 0.010 s | 0.023 s | 0.075 s |

(first call; the warm medians are within 10 %.)

**F-M2. Only a long window lets a painted cut come out as painted.**
[measure] A band of noise (1–2 kHz, 0.4 s) painted down; its level in the
result against the same band elsewhere:

| Window | painted −20 dB | painted −40 dB | removed |
|---|---|---|---|
| 5 ms | −18.6 dB | −30.0 dB | −32.0 dB |
| 32 ms | −19.6 dB | −39.6 dB | −89.8 dB |

With a 5 ms window, a removed band comes back at −32 dB: short windows
overlap so much in frequency that least squares refills the gap from its
edges. With 32 ms the cut is what was painted.

**F-M3. One harmonic can be taken out, partly.** [measure] The 10th
harmonic (1000 Hz) of a 100 Hz complex, removed over 970–1030 Hz for the
whole sound: −15.6 dB against its neighbours with a 32 ms window, −3.8 dB
with 5 ms. A 32 ms Hann window's main lobe is 125 Hz wide [read: 4 bins of
31.25 Hz], so a narrow cut leaves some of the harmonic; painting a wider
stroke removes more [inferred, not measured].

**F-M4. A mask fits easily in a link.** [measure] 256 × 256 cells
quantized to whole dB, deflated and base64-encoded: 112 characters with
nothing removed, 176 with a band and a harmonic removed. The recording
itself does not fit (F-M5).

**F-M5. A recording is too big for a link but fine in a saved file.**
[estimate] 10 s at 16 kHz as 16-bit samples is 320 000 bytes, about
427 000 characters as base64.

## Proposed design

### Interface (sketch)

```
┌ Speech │ Spectrogram │ Filter recording │ … ──────────── ▶ ■  ⤓ ⟲ ┐
│ Erase parts of a recording's spectrogram and hear what is left.     │
│ 8k ┤▓▓▒▒░░▓▓▒▒░░▓▓▒▒░░▓▓▒▒░░▓▓▒▒░░│ Source                  │
│    │▓▓▒▒░░▓▓▒▒████████▒▒░░▓▓▒▒░░▓▓│  ◉ Speech tab's sound   │
│ 4k ┤▓▓▒▒░░▓▓▒▒████████▒▒░░▓▓▒▒░░▓▓│  ○ hello.wav (1.8 s)    │
│    │▒▒░░▓▓▒▒░░████████░░▓▓▒▒░░▓▓▒▒│  [Open recording…]      │
│  0 ┤▓▓▒▒░░▓▓▒▒░░▓▓▒▒░░▓▓▒▒░░▓▓▒▒░░│ Brush                   │
│    0 s                       1.8 s│  ◉ remove ○ restore     │
├───────────────────────────────────┤  size, softness, −60 dB │
│ result: waveform and spectrogram  │  [Clear]                │
└───────────────────────────────────┴─────────────────────────┘
```

- The recording's spectrogram (magma) fills the canvas; painted areas are
  shown darkened by the amount they are turned down, so the picture shows
  what should remain. The result's spectrogram below shows what did.
- Remove paints a gain (default −60 dB, removed); Restore paints 0 dB.
  The brush, undo, Clear and the grid are the Paint primitive's.

### The grid

Rows are equal steps of frequency from 0 Hz to Nyquist (256 rows, 31.25 Hz
each at 16 kHz, the spacing of a 32 ms STFT's bins), columns equal
fractions of the duration (256), so the mask stretches with the duration
as a painting does. A cell is a gain in dB from 0 down to −60, where −60
means removed. Between cells the gain is read bilinearly, in amplitude, at
each STFT coefficient (as in `measure_mask.py`).

### The recording

A recording is shared by the tabs that use one (`../app.md`, "Layout"),
kept in the page's memory and in a saved file, not in the document's
history (undo does not unload a recording). It is decoded in the browser,
mixed to mono, resampled to the page's sampling rate, and cut to 10 s
(D10), with a note when it was cut. Loading one sets the page's duration
to its length (the other tabs' drawings stretch, as they do when the
duration is changed by hand).

### Data model

```json
"mask": {
  "rows": 256, "columns": 256, "floor_db": -60, "window": 0.032,
  "source": "speech" | "recording",
  "levels": "<base64 of deflated bytes, one per cell: 0 = 0 dB ... 60 = removed>"
}
```

and, at the page level of a saved file (never in a link):

```json
"recording": {"name": "hello.wav", "fs": 16000, "samples": "<base64 of 16-bit PCM>"}
```

### Python side

`src/sonore_sketch/mask.py`, `synthesize(state) -> so.Sound`, as the other
tabs: it takes the source (the Speech tab's sound, made by `tracks.py`, or
the recording's samples), analyzes it with a `GaborFrame`, applies the
gains and resynthesizes. Tests: removing a band comes out at its painted
depth (F-M2, as a test); a blank mask gives back the source (an
unmodified STFT resynthesizes exactly [read: `STFT`'s docstring]); a
saved document gives the same samples in Python and from the page.

## Decisions

**F1. How a recording gets in.**
(a) Open an audio file;
(b) also record from the microphone;
(c) also drag and drop a file onto the canvas.
*Recommended:* (a) in this tab's first PR, then (b) and (c) as a follow-up
PR. The microphone is the quickest way to hear your own voice filtered,
but it needs a permission prompt and a recording control, which is a
separate piece of work.

**F2. What the tab filters before a recording is loaded.**
(a) nothing ("Open a recording to start");
(b) the Speech tab's current sound;
(c) a short example recording shipped with the app.
*Recommended:* (b). Play works at once, nothing needs a licence, and it
connects the tabs: draw a vowel on Speech, then take its third formant
out here. (c) needs a recording we may redistribute.

**F3. Where the recording is kept.**
*Recommended:* in the page's memory and in saved files (as 16-bit PCM,
about 427 kB of text for 10 s, F-M5), never in links. A link to a drawing
whose source was a recording opens with the mask and a note asking for the
recording; the Speech tab's sound is used until one is opened.

**F4. Frequency axis.**
(a) linear, 0 Hz to Nyquist, as the STFT the mask applies to;
(b) logarithmic, as the Spectrogram tab.
*Recommended:* (a). The mask acts on STFT bins, which are evenly spaced,
and harmonics are evenly spaced on it too, so taking out one harmonic is a
straight horizontal stroke. On a log axis the upper harmonics crowd
together.

**F5. The STFT's window.**
(a) 32 ms Hann, hop 8 ms;
(b) 5 ms;
(c) a choice between the two in the tab.
*Recommended:* (a). F-M2 and F-M3: with 5 ms a removed band comes back at
−32 dB and a removed harmonic at −3.8 dB, so the tab would not do what it
shows. The result spectrogram below stays wideband (5 ms), as on the
other tabs.

**F6. Duration.**
*Recommended:* the page's duration follows the source: a recording sets it
to its length (up to 10 s); with the Speech tab as source it is the page's
duration as now. One duration rule for the whole app (`../app.md`,
"Duration").

## Order of work

After the decisions, each a PR for Cho:

1. The tab with the Speech tab's sound as its source: the grid, the
   background spectrogram, Remove and Restore, `mask.py` and its tests,
   and the page check.
2. Opening a recording, keeping it in saved files, the link note.
3. The microphone and drag and drop (F1, if (b) and (c) are wanted).

## References

- sonore: `STFT` and `GaborFrame` (`src/sonore/frames/gabor.py`), `Mask`.
- `painted.md` (the Paint primitive), `../app.md` (D7, D8, D10).
- Griffin, D., & Lim, J. (1984). Signal estimation from modified short-time
  Fourier transform. *IEEE Transactions on Acoustics, Speech, and Signal
  Processing*, 32(2), 236–243. doi:10.1109/TASSP.1984.1164317. (The
  least-squares estimate from a modified STFT that `to_sound` computes.)
