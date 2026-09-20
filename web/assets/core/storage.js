// Player state persistence. Game mode only — codex mode never touches this.
// Every write is best-effort: if localStorage is unavailable (private mode,
// quota exceeded) the game keeps running against the in-memory copy.

var STORAGE_KEY = "lemi_state";
var CURRENT_VERSION = 1;

function freshState() {
  return { v: CURRENT_VERSION, cards: [], storylines: {}, ssr_shards: {} };
}

function migrate(raw) {
  // Older shapes must never lose collected cards.
  if (!raw || typeof raw !== "object") return freshState();
  return {
    v: CURRENT_VERSION,
    cards: Array.isArray(raw.cards) ? raw.cards.slice() : [],
    storylines: raw.storylines && typeof raw.storylines === "object"
      ? raw.storylines : {},
    ssr_shards: raw.ssr_shards && typeof raw.ssr_shards === "object"
      ? raw.ssr_shards : {},
  };
}

function createStorage(backend) {
  var state = freshState();
  try {
    var text = backend.getItem(STORAGE_KEY);
    if (text) state = migrate(JSON.parse(text));
  } catch (e) {
    state = freshState();   // unreadable or corrupt: start clean, do not crash
  }

  function persist() {
    try {
      backend.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      // Quota or security error: in-memory state stays authoritative.
    }
  }

  return {
    load: function () { return state; },
    save: function (next) { state = next; persist(); },
    addCard: function (id) {
      if (state.cards.indexOf(id) !== -1) return false;
      state.cards.push(id);
      persist();
      return true;
    },
    hasCard: function (id) { return state.cards.indexOf(id) !== -1; },
    cardCount: function () { return state.cards.length; },
    setTile: function (slId, n) {
      if (!state.storylines[slId]) state.storylines[slId] = { tile: 0, done: false };
      state.storylines[slId].tile = n;
      persist();
    },
    migrate: migrate,
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { createStorage: createStorage, migrate: migrate,
                     CURRENT_VERSION: CURRENT_VERSION };
} else if (typeof window !== "undefined") {
  window.LemiStorage = { createStorage: createStorage,
                         CURRENT_VERSION: CURRENT_VERSION };
}
