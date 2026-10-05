// The page's log: what the page did and what went wrong, kept in memory so
// a problem can be read on the page and copied into a bug report. Nothing
// leaves the browser unless the person copies it.

const LIMIT = 300;

export class Log {
  constructor() {
    this.entries = [];
    this.errors = 0;
    this.onchange = () => {};
  }

  add(level, text, detail = "") {
    const time = new Date().toISOString().slice(11, 23);
    this.entries.push({ time, level, text, detail });
    if (this.entries.length > LIMIT) this.entries.shift();
    if (level === "error") this.errors++;
    this.onchange();
  }

  info(text, detail) {
    this.add("info", text, detail);
  }

  error(text, detail) {
    this.add("error", text, detail);
  }

  clear() {
    this.entries = [];
    this.errors = 0;
    this.onchange();
  }

  // The log as plain text, one entry per line, details indented beneath.
  text() {
    return this.entries
      .map(({ time, level, text, detail }) => {
        const line = `${time} ${level === "error" ? "ERROR" : "info "} ${text}`;
        return detail ? `${line}\n${detail.replace(/^/gm, "    ")}` : line;
      })
      .join("\n");
  }
}
