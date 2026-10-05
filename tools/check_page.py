"""Check the page in a headless Chromium: it loads, draws, plays and undoes.

This drives the real page (index.html) the way a person would, with
Playwright, and fails on any error in the browser console. By default it uses
the local engine (``?engine=local``: sonore in this Python, through
tools/serve.py), which needs no network; ``--engine pyodide`` loads Pyodide
and sonore from their CDNs in the browser, as visitors to the page do.

    pip install -e . playwright
    python tools/check_page.py                     # local engine
    python tools/check_page.py --engine pyodide    # needs cdn.jsdelivr.net and PyPI
    python tools/check_page.py --screenshot page.png

It starts tools/serve.py itself on a free port.
"""

from __future__ import annotations

import argparse
import base64
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def document_in(page) -> dict:
    """The drawing the page holds, read back from its link (#state=...)."""
    state = page.evaluate("location.hash").split("state=")[1]
    return json.loads(base64.urlsafe_b64decode(state + "=" * (-len(state) % 4)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--engine", choices=["local", "pyodide"], default="local")
    parser.add_argument("--pyodide-url", help="Pyodide's full/ folder, instead of jsDelivr (with --engine pyodide)")
    parser.add_argument("--chromium", help="path to a Chromium to use instead of Playwright's own")
    parser.add_argument("--screenshot", help="save a screenshot of the page here at the end")
    parser.add_argument("--headed", action="store_true", help="show the browser")
    args = parser.parse_args()

    from playwright.sync_api import expect, sync_playwright

    port = free_port()
    server = subprocess.Popen([sys.executable, str(ROOT / "tools" / "serve.py"), "--port", str(port)], stdout=subprocess.DEVNULL)
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=not args.headed, executable_path=args.chromium)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.on("console", lambda m: m.type == "error" and errors.append(m.text))
            page.on("pageerror", lambda e: errors.append(str(e)))
            for attempt in range(50):
                try:
                    extra = f"&pyodide={args.pyodide_url}" if args.pyodide_url else ""
                    page.goto(f"http://127.0.0.1:{port}/?engine={args.engine}{extra}")
                    break
                except Exception:
                    time.sleep(0.1)
            start = time.perf_counter()
            status = page.locator("#status")
            expect(status).to_contain_text("Made", timeout=180_000)
            print(f"ready and first sound made in {time.perf_counter() - start:.1f} s: {page.locator('#versions').inner_text()}")

            formants = page.locator(".panel-formants svg")
            box = formants.bounding_box()
            doc = document_in(page)
            x_of = lambda t: box["x"] + 52 + t / doc["duration"] * (box["width"] - 62)  # noqa: E731
            y_of = lambda hz: box["y"] + box["height"] - 8 - hz / 5000 * (box["height"] - 16)  # noqa: E731

            # Point: drag F2's breakpoint at 0.45 s from 2000 Hz up to 2300 Hz.
            page.keyboard.press("2")
            page.keyboard.press("p")
            page.mouse.move(x_of(0.45), y_of(2000))
            page.mouse.down()
            page.mouse.move(x_of(0.45), y_of(2300), steps=5)
            page.mouse.up()
            f2 = document_in(page)["params"]["F2"]
            assert abs(f2[1][2] - 2300) < 30, f"F2 breakpoint not dragged: {f2}"
            print(f"point: F2 at 0.45 s dragged to {f2[1][2]:.0f} Hz")

            # Line: F3 replaced between 0.1 s and 0.5 s.
            page.keyboard.press("3")
            page.keyboard.press("l")
            page.mouse.move(x_of(0.1), y_of(2400))
            page.mouse.down()
            page.mouse.move(x_of(0.5), y_of(3000), steps=5)
            page.mouse.up()
            f3 = document_in(page)["params"]["F3"]
            assert len(f3[0]) == 4 and abs(f3[1][1] - 2400) < 30 and abs(f3[1][2] - 3000) < 30, f3
            print(f"line: F3 is now {f3}")

            # Freehand on the F0 strip: a rise and fall becomes a few breakpoints.
            strip = page.locator(".panel-F0 svg").bounding_box()
            sx = lambda t: strip["x"] + 52 + t / doc["duration"] * (strip["width"] - 62)  # noqa: E731
            sy = lambda hz: strip["y"] + strip["height"] - 8 - hz / 300 * (strip["height"] - 16)  # noqa: E731
            page.keyboard.press("f")
            page.mouse.move(sx(0.05), sy(110))
            page.mouse.down()
            for i in range(1, 41):
                t = 0.05 + 0.5 * i / 40
                page.mouse.move(sx(t), sy(110 + 60 * (1 - abs(2 * i / 40 - 1))))
            page.mouse.up()
            f0 = document_in(page)["params"]["F0"]
            assert 3 <= len(f0[0]) <= 12 and max(f0[1]) > 150, f"freehand F0 not simplified as expected: {f0}"
            print(f"freehand: F0 has {len(f0[0])} breakpoints, peak {max(f0[1]):.0f} Hz")
            expect(status).to_contain_text("Made", timeout=60_000)

            # Bandwidths: the strip shows the selected formant's, here B1.
            page.check(".show-bandwidths")
            page.keyboard.press("1")
            page.keyboard.press("l")
            bw = page.locator(".panel-bandwidths svg").bounding_box()
            bx = lambda t: bw["x"] + 52 + t / doc["duration"] * (bw["width"] - 62)  # noqa: E731
            by = lambda hz: bw["y"] + bw["height"] - 8 - hz / 600 * (bw["height"] - 16)  # noqa: E731
            page.mouse.move(bx(0), by(60))
            page.mouse.down()
            page.mouse.move(bx(0.6), by(300), steps=5)
            page.mouse.up()
            b1 = document_in(page)["params"]["B1"]
            assert abs(b1[1][0] - 60) < 10 and abs(b1[1][-1] - 300) < 10, b1
            print(f"bandwidth: B1 is now {b1}")
            page.keyboard.press("Control+z")
            page.uncheck(".show-bandwidths")

            # Undo the stroke, then redo it.
            page.keyboard.press("Control+z")
            assert document_in(page)["params"]["F0"] == doc["params"]["F0"], "undo did not restore F0"
            page.keyboard.press("Control+Shift+z")
            assert document_in(page)["params"]["F0"] == f0, "redo did not bring F0 back"
            print("undo and redo: ok")

            # Duration: stretching scales every breakpoint time.
            page.fill("#duration", "1.2")
            page.press("#duration", "Enter")
            stretched = document_in(page)
            assert stretched["duration"] == 1.2 and stretched["params"]["F3"][0] == [round(2 * t, 4) for t in f3[0]]
            print("duration: stretched to 1.2 s")

            # Play makes a sound and shows Stop while it plays.
            page.click("#play")
            expect(page.locator("#play")).to_have_text("■ Stop", timeout=60_000)
            expect(page.locator("#play")).to_have_text("▶ Play", timeout=10_000)
            print("play: played and ended")

            drawn = page.evaluate(
                """() => ['waveform', 'spectrogram'].map((id) => {
                    const c = document.getElementById(id);
                    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
                    let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i]) n++;
                    return n; })"""
            )
            assert all(drawn), f"result pictures are empty: {drawn}"
            print(f"result pictures drawn ({drawn[0]} and {drawn[1]} pixels)")

            # A link from before breakpoint times were kept increasing (two F0
            # points at 0.3 s) is tidied on opening, and synthesizes.
            def open_link(state):
                encoded = base64.urlsafe_b64encode(json.dumps(state).encode()).decode().rstrip("=")
                page.goto(f"http://127.0.0.1:{port}/?engine={args.engine}{extra}#state={encoded}")
                page.reload()

            repeated = {**doc, "params": {**doc["params"], "F0": [[0, 0.3, 0.3, 0.6], [125, 100, 140, 95]]}}
            open_link(repeated)
            expect(status).to_contain_text("Made", timeout=180_000)
            assert document_in(page)["params"]["F0"] == [[0, 0.3, 0.6], [125, 140, 95]], document_in(page)["params"]["F0"]
            print("repeated breakpoint times in a link: tidied and synthesized")

            # A drawing sonore refuses (F1 above Nyquist at fs = 1000 Hz) puts
            # the error and its traceback in the log, and Reset recovers.
            before_failure = len(errors)
            open_link({**doc, "fs": 1000})
            expect(status).to_contain_text("Synthesis failed", timeout=180_000)
            expect(page.locator("#log-toggle")).to_have_text("Log (1)")
            page.click("#log-toggle")
            expect(page.locator("#log-lines .error")).to_contain_text("synthesis failed")
            assert "Traceback" in page.locator("#log-lines .error").inner_text(), "no traceback in the log"
            print("error: shown in the log with its traceback")
            page.click("#reset")
            expect(status).to_contain_text("Made", timeout=60_000)
            assert document_in(page) == doc, "Reset did not restore the default drawing"
            page.keyboard.press("Control+z")
            assert document_in(page)["fs"] == 1000, "Undo did not bring the drawing back after Reset"
            print("reset: back to the default drawing, and undo brings the old one back")
            # The local server answers the refused drawing (twice: opened, then
            # undone back to) with HTTP 400, which the browser reports in its
            # console; those are expected.
            page.wait_for_timeout(500)
            errors[before_failure:] = [e for e in errors[before_failure:] if "400 (Bad Request)" not in e]
            if args.screenshot:
                page.screenshot(path=args.screenshot)
            browser.close()
    finally:
        server.terminate()
    if errors:
        sys.exit("errors in the browser console:\n" + "\n".join(errors))
    print("page check passed")


if __name__ == "__main__":
    main()
