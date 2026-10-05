// Pictures of a result: a spectrogram image and a waveform, on canvases.

// Size a canvas's backing store to its displayed size; returns its context.
export function fitCanvas(canvas) {
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(1, Math.round(canvas.clientWidth * ratio));
  const height = Math.max(1, Math.round(canvas.clientHeight * ratio));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  return canvas.getContext("2d");
}

// Draw `picture` (8-bit levels, rows from 0 Hz up) over time [0, duration]
// and frequency [0, fTop], dark where loud. `alpha` makes it a background.
export function drawSpectrogram(canvas, picture, duration, fTop, alpha = 1) {
  const context = fitCanvas(canvas);
  const { width, height } = canvas;
  context.clearRect(0, 0, width, height);
  if (!picture) return;
  const { data, nFreqs, nFrames, fMax, tStart, tStep } = picture;
  const image = context.createImageData(width, height);
  const dark = getComputedStyle(canvas).getPropertyValue("--ink-rgb").trim() || "20, 24, 31";
  const [r, g, b] = dark.split(",").map(Number);
  for (let x = 0; x < width; x++) {
    const t = ((x + 0.5) / width) * duration;
    const frame = Math.round((t - tStart) / tStep);
    if (frame < 0 || frame >= nFrames) continue;
    for (let y = 0; y < height; y++) {
      const f = (1 - (y + 0.5) / height) * fTop;
      const row = Math.round((f / fMax) * (nFreqs - 1));
      if (row < 0 || row >= nFreqs) continue;
      const level = data[row * nFrames + frame] / 255;
      const i = 4 * (y * width + x);
      image.data[i] = r;
      image.data[i + 1] = g;
      image.data[i + 2] = b;
      image.data[i + 3] = Math.round(255 * alpha * level ** 1.5);
    }
  }
  context.putImageData(image, 0, 0);
}

// The waveform as a min-max envelope per pixel column.
export function drawWaveform(canvas, samples, fs, duration) {
  const context = fitCanvas(canvas);
  const { width, height } = canvas;
  context.clearRect(0, 0, width, height);
  if (!samples) return;
  let peak = 0;
  for (const x of samples) peak = Math.max(peak, Math.abs(x));
  if (!peak) return;
  context.fillStyle = getComputedStyle(canvas).getPropertyValue("--wave").trim() || "#2e86ab";
  const middle = height / 2;
  for (let x = 0; x < width; x++) {
    const a = Math.floor(((x / width) * duration) * fs);
    const b = Math.min(samples.length, Math.floor((((x + 1) / width) * duration) * fs));
    let lo = 0;
    let hi = 0;
    for (let i = a; i < b; i++) {
      lo = Math.min(lo, samples[i]);
      hi = Math.max(hi, samples[i]);
    }
    const top = middle - (hi / peak) * middle * 0.95;
    const bottom = middle - (lo / peak) * middle * 0.95;
    context.fillRect(x, top, 1, Math.max(1, bottom - top));
  }
}
