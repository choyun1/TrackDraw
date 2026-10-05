// A drawing in a link: #state=<base64url of the JSON> (docs/design/app.md, D8).

export function encodeState(state) {
  const bytes = new TextEncoder().encode(JSON.stringify(state));
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function decodeState(text) {
  const base64 = text.replace(/-/g, "+").replace(/_/g, "/");
  const binary = atob(base64 + "=".repeat((4 - (base64.length % 4)) % 4));
  const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
}

// The state in a location hash, or null if it has none.
export function stateFromHash(hash) {
  const match = /(?:^#|&)state=([A-Za-z0-9_-]+)/.exec(hash);
  return match ? decodeState(match[1]) : null;
}
