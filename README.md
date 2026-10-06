# sonore sketch

Draw on a picture of sound and hear the result. Each tab is one of
[sonore](https://pypi.org/project/sonore/)'s routes back to sound, given a
point-and-click surface; sonore does the synthesis, in your browser.

**Speech** is the first tab: draw formant (F1–F5), F0, voicing amplitude
(AV) and bandwidth tracks over time, and hear the speech Klatt's (1980)
synthesizer makes from them. It follows Track-Draw (Assmann, Ballard,
Bornstein & Paschall, 1994). **Spectrogram** lets you paint level on time ×
log-frequency and hear a sound whose spectrotemporal envelope is the
painting (sonore's `ripple_sound`). **Modulation** lets you place blobs on
a modulation spectrum (rate × density) and hear a sound with that
modulation (sonore's `ModulationSpectrum.from_blobs`). Spectrogram masks are
planned (`docs/design/app.md`).

## Using it

Open **https://choyun1.github.io/sonore-sketch/**, published from `main`
by `.github/workflows/pages.yml`. The page is static, so you can also serve
the repository's root yourself and open `index.html`:

    python tools/serve.py        # http://localhost:8000/

The first visit loads Python (Pyodide), NumPy, SciPy and sonore into the
browser, which takes 10–20 s; you can draw while it loads. After that,
each change is heard as soon as you finish drawing it.

- **Point** adds a breakpoint or drags one; double-click removes it.
  With any tool, dragging a breakpoint's circle up or down moves it; with
  Line or Freehand, dragging from a circle along time draws from it instead.
  **Line** replaces a span by a straight line. **Freehand** draws a stroke,
  kept as the fewest breakpoints within a small tolerance.
- The selected track is the one you draw on. Select it with its button,
  by clicking its line, or with the keys 1–5 for F1–F5.
- In **Spectrogram**, drag to paint at the brush's level (0 dB is the loudest),
  and right-drag or **Erase** to paint silence. **Clear** erases everything.
  The carrier is what the painting shapes: tones, harmonics of an F0, or
  noise. The harmonic carrier sounds only at multiples of F0, which show as
  faint dashed lines; paint between them is silent.
- The duration (up to 10 s) stretches everything drawn.
- **Save** writes the drawing as JSON, **Open** reads it back, **Link**
  copies an address that opens it, and **WAV** saves the sound.
- **Reset** starts the tab you are on again from its default drawing, at
  the default duration; Undo brings yours back.
- **Log** shows what the page did and any errors, with Python's traceback.
  **Copy** puts the log, the versions and the current drawing on the
  clipboard, for a bug report.

A saved drawing gives the same sound in Python:

```python
import json
from sonore_sketch import page

sound = page.synthesize(json.load(open("sketch.json")))
```

## Developing

```
pip install -e ".[test]" playwright
python -m pytest                  # the Python half, against sonore directly
npm test                          # the page's model (Node 20+, no packages)
python tools/check_page.py        # the page in headless Chromium
```

`python tools/serve.py` also serves `?engine=local`, which runs the
synthesis in your own Python instead of the browser: no download, and it
works offline. `tools/check_page.py` uses it by default; add
`--engine pyodide` to test the page as visitors get it.

The designs are in `docs/design/`, and the scripts behind their
measurements in `tools/`.

## Credits

sonore sketch grew out of TrackDraw (2016), by Adrian Y. Cho and Daniel R
Guest, whose history this repository keeps. The Speech tab is after:

Assmann, P., Ballard, W., Bornstein, L., & Paschall, D. (1994). Track-Draw:
A graphical interface for controlling the parameters of a speech
synthesizer. *Behavior Research Methods, Instruments, & Computers*, 26(4),
431–436. doi:10.3758/BF03204661.

This project is AI-assisted: much of the code and documentation was drafted
by Claude (Claude Code) for Cho to review. MIT licence (`LICENSE.txt`).
