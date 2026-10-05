# sonore sketch

Draw on a picture of sound and hear the result. Each tab is one of
[sonore](https://pypi.org/project/sonore/)'s routes back to sound, given a
point-and-click surface; sonore does the synthesis, in your browser.

**Tracks** is the first tab: draw formant (F1–F5), F0, voicing amplitude
(AV) and bandwidth tracks over time, and hear the speech Klatt's (1980)
synthesizer makes from them. It follows Track-Draw (Assmann, Ballard,
Bornstein & Paschall, 1994). Painted spectrograms, spectrogram masks and
modulation-spectrum blobs are planned (`docs/design/app.md`).

## Using it

The page is static: serve the repository's root and open `index.html`.

    python tools/serve.py        # http://localhost:8000/

The first visit loads Python (Pyodide), NumPy, SciPy and sonore into the
browser, which takes 10–20 s; you can draw while it loads. After that,
each change is heard as soon as you finish drawing it.

- **Point** adds a breakpoint or drags one; double-click removes it.
  **Line** replaces a span by a straight line. **Freehand** draws a stroke,
  kept as the fewest breakpoints within a small tolerance.
- The selected track is the one you draw on. Select it with its button,
  by clicking its line, or with the keys 1–5 for F1–F5.
- The duration (up to 10 s) stretches everything drawn.
- **Save** writes the drawing as JSON, **Open** reads it back, **Link**
  copies an address that opens it, and **WAV** saves the sound.

A saved drawing gives the same sound in Python:

```python
import json
from sonore_sketch import tracks

sound = tracks.synthesize(json.load(open("tracks.json")))
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
Guest, whose history this repository keeps. The Tracks tab is after:

Assmann, P., Ballard, W., Bornstein, L., & Paschall, D. (1994). Track-Draw:
A graphical interface for controlling the parameters of a speech
synthesizer. *Behavior Research Methods, Instruments, & Computers*, 26(4),
431–436. doi:10.3758/BF03204661.

This project is AI-assisted: much of the code and documentation was drafted
by Claude (Claude Code) for Cho to review. MIT licence (`LICENSE.txt`).
