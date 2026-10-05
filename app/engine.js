// Where synthesis runs. "pyodide" (the default): sonore in a Web Worker in
// this browser. "local": tools/serve.py runs the same Python natively, for
// working offline or testing without the Pyodide CDN (?engine=local).
//
// Both resolve a request {tab, state} to
// {fs, samples: Float32Array, synthesisSeconds, spectrogram: {...}}.

function bytesFromBase64(text) {
  const binary = atob(text);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

class PyodideEngine {
  constructor({ onProgress, onReady, onFailed }) {
    const url = new URL("./worker.js", import.meta.url);
    const pyodide = new URLSearchParams(location.search).get("pyodide");
    if (pyodide) url.searchParams.set("pyodide", pyodide);
    this.worker = new Worker(url, { type: "module" });
    this.waiting = new Map();
    this.nextId = 0;
    this.worker.onmessage = ({ data }) => {
      if (data.type === "progress") return onProgress(data.text);
      if (data.type === "ready") return onReady(data.versions);
      if (data.type === "failed") {
        onFailed(data.message);
        for (const { reject } of this.waiting.values()) reject(new Error(data.message));
        this.waiting.clear();
        return;
      }
      const { resolve, reject } = this.waiting.get(data.id);
      this.waiting.delete(data.id);
      if (data.type === "result") resolve(data.result);
      else reject(Object.assign(new Error(data.message), { detail: data.detail }));
    };
    this.worker.onerror = (event) => onFailed(event.message ?? "the synthesis worker failed");
  }

  synthesize(request) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.waiting.set(id, { resolve, reject });
      this.worker.postMessage({ id, request });
    });
  }
}

class LocalEngine {
  constructor({ onProgress, onReady, onFailed }) {
    onProgress("Connecting to the local server…");
    fetch("api/version")
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error(`HTTP ${response.status}`))))
      .then(({ versions }) => onReady(`${versions} (local server)`))
      .catch((error) => onFailed(`no local server (run python tools/serve.py): ${error.message}`));
  }

  async synthesize(request) {
    const response = await fetch("api/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    const body = await response.json();
    if (!response.ok) throw Object.assign(new Error(body.error), { detail: body.detail });
    return {
      fs: body.fs,
      samples: new Float32Array(bytesFromBase64(body.samples).buffer),
      synthesisSeconds: body.synthesis_s,
      spectrogram: {
        data: bytesFromBase64(body.spectrogram.data),
        nFreqs: body.spectrogram.n_freqs,
        nFrames: body.spectrogram.n_frames,
        fMax: body.spectrogram.f_max,
        tStart: body.spectrogram.t_start,
        tStep: body.spectrogram.t_step,
      },
    };
  }
}

export function createEngine(kind, callbacks) {
  return kind === "local" ? new LocalEngine(callbacks) : new PyodideEngine(callbacks);
}

// Only the newest request matters while one is running: older waiting ones
// resolve to null instead of being synthesized.
export class LatestOnly {
  constructor(engine) {
    this.engine = engine;
    this.running = false;
    this.pending = null;
  }

  synthesize(request) {
    return new Promise((resolve, reject) => {
      this.pending?.resolve(null);
      this.pending = { request, resolve, reject };
      this.next();
    });
  }

  async next() {
    if (this.running || !this.pending) return;
    const { request, resolve, reject } = this.pending;
    this.pending = null;
    this.running = true;
    try {
      resolve(await this.engine.synthesize(request));
    } catch (error) {
      reject(error);
    } finally {
      this.running = false;
      this.next();
    }
  }
}
