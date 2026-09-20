// Game loop. One roll produces an ordered list of events, one per tile
// walked. Every tile on the path fires, including POIs passed in the
// middle of a move — the die sets the pace, never the content.

var STORYLINE_ID = "emily-in-paris";

function _req(path, globalName, key) {
  if (typeof require !== "undefined") return require(path)[key];
  return window[globalName][key];
}

function createGame(payload, storage, deps) {
  var rollDice = _req("./dice.js", "LemiDice", "rollDice");
  var resolveMove = _req("./dice.js", "LemiDice", "resolveMove");
  var resolveTile = _req("./tiles.js", "LemiTiles", "resolveTile");
  var isNight = _req("./tiles.js", "LemiTiles", "isNight");

  var board = payload.board || [];
  var nightFrom = payload.night_from_index;
  var lang = (deps && deps.lang) || "zh";
  var camera = deps && deps.camera;
  var rng = deps && deps.rng;

  var saved = storage.load().storylines[STORYLINE_ID];
  var position = saved ? saved.tile : 0;

  // Resolve one tile into an event, running the same side effects a walked
  // tile does: pitch the camera on POIs and de-dupe card collection.
  function _visit(idx) {
    var tile = board[idx];
    var resolved = resolveTile(tile, payload, lang);
    if (camera) camera.moveTo(tile, tile.type === "poi");

    var isNew = false;
    if (resolved.kind === "card") {
      isNew = storage.addCard(resolved.content.id);
    }
    return {
      tileIndex: idx,
      kind: resolved.kind,
      durationMs: resolved.durationMs,
      content: resolved.content,
      isNew: isNew,
      night: isNight(idx, nightFrom),
      finished: idx === board.length - 1,
    };
  }

  // The board's first tile is where Emily wakes up — resolveMove's path
  // always starts at from+1, so tile 0 is never walked and its card would
  // be lost. start() fires that opening tile explicitly. It's idempotent:
  // storage.addCard already returns false on a card we own, so replaying
  // simply reports isNew=false without double-collecting.
  function start() {
    if (!board.length) return Promise.resolve([]);
    return Promise.resolve([_visit(0)]);
  }

  function roll() {
    var move = resolveMove(position, rollDice(rng), board.length);
    var events = [];
    move.path.forEach(function (idx) {
      events.push(_visit(idx));
    });
    position = move.to;
    storage.setTile(STORYLINE_ID, position);
    return Promise.resolve(events);
  }

  return {
    start: start,
    roll: roll,
    state: function () {
      return { position: position, finished: position >= board.length - 1,
               night: isNight(position, nightFrom) };
    },
    reset: function () {
      position = 0;
      storage.setTile(STORYLINE_ID, 0);
    },
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { createGame: createGame };
} else if (typeof window !== "undefined") {
  window.LemiGame = { createGame: createGame };
}
