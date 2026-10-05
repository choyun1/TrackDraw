// The page's document: what Save writes, what a link holds, and what undo
// steps through (docs/design/tabs/painted.md, "Data model"). The duration and
// sampling rate belong to the page; each tab keeps its own section, so you
// can switch tabs and come back to what you drew.
//
//   {"app": "sonore-sketch", "version": 2, "sonore": "0.5.0",
//    "duration": 0.6, "fs": 16000, "tab": "tracks",
//    "tracks": {"mode": "klatt", "params": {...}}}
//
// A tab works on its own state, the shape its Python function takes
// (sonore_sketch.page.tab_state does the same in Python). A version-1
// document, the Tracks tab's own format from before there were other tabs,
// opens as version 2, so old files and links keep working.
//
// No DOM here, so this file runs under `node --test`.

import * as tracks from "./tracks/model.js";

export const APP = "sonore-sketch";
export const VERSION = 2;
export const TABS = ["tracks"];

export function defaultPage() {
  const { sonore, duration, fs, mode, params } = tracks.defaultDocument();
  return { app: APP, version: VERSION, sonore, duration, fs, tab: "tracks", tracks: { mode, params } };
}

// A document from a file or a link, as version 2; throws an Error saying what
// is wrong with it.
export function upgrade(doc) {
  if (doc?.trackdraw === tracks.FORMAT) {
    const { sonore, duration, fs, mode = "klatt", params = {} } = doc;
    return { app: APP, version: VERSION, sonore, duration, fs, tab: "tracks", tracks: { mode, params } };
  }
  if (doc?.app !== APP || doc.version !== VERSION) {
    throw new Error(`not a sonore sketch document of version ${VERSION}, or a TrackDraw document of format ${tracks.FORMAT}`);
  }
  return doc;
}

// The state a tab draws on and its Python function takes.
export function tabState(page, tab) {
  if (tab === "tracks") {
    const { sonore, duration, fs } = page;
    return { trackdraw: tracks.FORMAT, sonore, duration, fs, ...page.tracks };
  }
  throw new Error(`unknown tab ${tab}`);
}

// A new page with a tab's state put back.
export function withTabState(page, tab, state) {
  if (tab === "tracks") {
    const { mode, params } = state;
    return { ...page, tracks: { mode, params } };
  }
  throw new Error(`unknown tab ${tab}`);
}

// Check and tidy a document from a file or a link (upgrading it if old).
export function openDocument(doc) {
  const page = upgrade(doc);
  const state = tracks.tidyDocument(tracks.check(tabState(page, "tracks")));
  return withTabState({ ...page, tab: TABS.includes(page.tab) ? page.tab : "tracks" }, "tracks", state);
}

// Change the duration, stretching what every tab has drawn.
export function stretchPage(page, duration) {
  const state = tracks.stretch(tabState(page, "tracks"), duration);
  return withTabState({ ...page, duration }, "tracks", state);
}
