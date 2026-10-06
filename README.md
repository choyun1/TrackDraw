# sonore sketch

Draw on a picture of sound and hear the result.

**Try it: https://choyun1.github.io/sonore-sketch/**

Each tab is one of [sonore](https://pypi.org/project/sonore/)'s routes back
to sound, given a point-and-click surface. sonore does the synthesis, in
your browser (Python under Pyodide); this project is only the interface.
There is nothing to install.

## The tabs

| Tab | You draw | You hear | State |
|---|---|---|---|
| **Speech** | formant (F1–F5), F0, voicing (AV) and bandwidth tracks over time | the speech Klatt's (1980) synthesizer makes from them, after Track-Draw (Assmann et al., 1994) | built |
| **Spectrogram** | level painted on time × log-frequency | a sound whose spectrogram is the painting (sonore's `ripple_sound`) | built |
| **Filter recording** | erasures on a recording's spectrogram | what is left of the recording | designed, not built |
| **Modulation** | blobs on a modulation spectrum (rate × density), and optional frequency bands | a sound with that modulation (sonore's `ModulationSpectrum.from_blobs`), confined to the bands | built |
| **Edit modulation** | cuts on a sound's modulation spectrum (a syllable train, the Speech tab's sound, or a recording) | the sound with that modulation taken out (sonore's `ModulationSpectrum.with_gain`) | built |

Tabs that are not built yet are greyed out on the page.

## Using it

The first visit loads Python, NumPy, SciPy and sonore into the browser,
which takes 10–20 s; you can draw while it loads. After that, a sound is
made each time you finish a change.

**On every tab**

- **Play** (or Space) plays the sound. Tick **Auto-play** to hear each
  change as soon as it is drawn (for sounds up to 3 s).
- The **duration** (up to 10 s) stretches everything drawn.
- **Undo** and **Redo** (Ctrl+Z, Ctrl+Shift+Z or Ctrl+Y) cover every change.
  **Reset** starts the tab you are on again from its default drawing, at
  the default duration; Undo brings yours back.
- **Save** writes the drawing as JSON, **Open** reads it back, **Link**
  copies an address that opens it, and **WAV** saves the sound.
- **Log** shows what the page did and any errors, with Python's traceback.
  Its **Copy** puts the log, the versions and the current drawing on the
  clipboard, for a bug report.

**Speech.** Select a track with its button, by clicking its line, or with
the keys 1–5 for F1–F5. **Point** adds a breakpoint or drags one;
double-click removes it. **Line** replaces a span with a straight line.
**Freehand** draws a stroke, kept as the fewest breakpoints within a small
tolerance. With any tool, dragging a breakpoint's circle up or down moves
it; with Line or Freehand, dragging from a circle along time draws from it
instead.

**Spectrogram.** Drag to paint at the brush's level (0 dB is the loudest);
right-drag or **Erase** paints silence, and **Clear** erases everything.
Size and Softness shape the brush. The **carrier** is what the painting
shapes: log-spaced tones, harmonics of an F0, or noise. The harmonic
carrier sounds only at multiples of F0, which show as faint dashed lines;
paint between them is silent.

**Modulation.** The **Design** panels are what you draw: click the plane to
add a blob, drag it to move it, and drag its squares to change its width
and height (up to 8 blobs). **Add band** confines the sound to a band of
frequencies that you reshape on the spectrogram with Point, Line or
Freehand. The **Result** panels are measured from the sound that came out:
its own modulation spectrum and its waveform, beside what you drew. The
carrier (tones, harmonic or noise), the modulation depth, and the seed
(**New draw** hears another random draw with the same spectrum) are below.

**Edit modulation.** Choose a **source**: a syllable train made at the
page's duration, the Speech tab's sound, or a recording (**Open audio
file…**, which sets the duration to the recording's, up to 10 s). Each
sound made shows the source's modulation spectrum on the plane, with a
centre strip for rates under 1 Hz. Paint on it to erase that modulation
(right-drag or **Restore** brings it back); **Erase**'s **Depth** goes down
to -60 dB, which removes it. The presets replace the mask: keep the rates
below some Hz, or remove the downward or upward sweeps. The **carrier** is
the source's own fine structure, tones or noise; **Iterations** search for
a sound whose own modulation comes closer to the edit, which the source's
own fine structure needs to be heard well. The **Result** panels show the
sound that came out: its own modulation spectrum, measured, with the cuts
outlined over it, its spectrogram and its waveform. When an edit needs
envelopes below zero, sonore clips them and a note under the plane says how
much. A recording is kept in saved files but never in links.

## The same sound in Python

A saved drawing gives the same sound outside the browser:

```python
import json
from sonore_sketch import page

sound = page.synthesize(json.load(open("sketch.json")))
```

## Developing

The page is static: `index.html` and the ES modules in `app/`, with no
build step and no JavaScript dependencies. The Python half, which the page
runs under Pyodide, is in `src/sonore_sketch/` (one module per tab, and
`page.py`, which the page calls). It needs sonore 0.5.

```
pip install -e ".[test]" playwright
python tools/serve.py             # the page at http://localhost:8000/
python -m pytest                  # the Python half, against sonore directly
npm test                          # the page's model (Node 20+, no packages)
python tools/check_page.py        # the page in headless Chromium
```

Open `http://localhost:8000/?engine=local` to run the synthesis in your
own Python instead of the browser: no download, and it works offline.
`tools/check_page.py` uses the local engine by default; add
`--engine pyodide` to test the page as visitors get it. CI runs all three
test commands on every pull request (`.github/workflows/test.yml`), and
`main` is published to GitHub Pages (`.github/workflows/pages.yml`).

Two things to keep in step:

- The sonore version is pinned twice, in `pyproject.toml` and as
  `SONORE_VERSION` in `app/worker.js`.
- `PYTHON_FILES` in `app/worker.js` lists every module in
  `src/sonore_sketch/`. A new module must be added there, or the page fails
  in the browser while the local engine still works.

## Design documents

Every tab is designed before it is built, in `docs/design/`: `app.md` for
the page as a whole, and `tabs/` for each tab (`tracks.md` for Speech,
`painted.md` for Spectrogram, `blobs.md` and `bands.md` for Modulation,
`edit.md` for Edit modulation).
Each records the measurements behind it, made by the scripts in `tools/`,
and the decisions Cho made. The design of Filter recording is still in
review as a pull request.

## Credits

sonore sketch grew out of TrackDraw (2016), by Adrian Y. Cho and Daniel R
Guest, whose history this repository keeps. The Speech tab is after:

Assmann, P., Ballard, W., Bornstein, L., & Paschall, D. (1994). Track-Draw:
A graphical interface for controlling the parameters of a speech
synthesizer. *Behavior Research Methods, Instruments, & Computers*, 26(4),
431–436. doi:10.3758/BF03204661.

Klatt, D. H. (1980). Software for a cascade/parallel formant synthesizer.
*Journal of the Acoustical Society of America*, 67(3), 971–995.
doi:10.1121/1.383940.

This project is AI-assisted: much of the code and documentation was drafted
by Claude (Claude Code) for Cho to review. MIT licence (`LICENSE.txt`).
