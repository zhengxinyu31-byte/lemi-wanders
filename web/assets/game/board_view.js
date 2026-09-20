// Pure helpers for drawing the board. ui.js does the DOM/MapLibre wiring;
// every decision that can be a plain function lives here so it can be tested
// without a browser — the board was the one layer that shipped untested and
// three severe bugs slipped through as a result.

// Tile types, most prominent first. POI squares are the destinations and
// read largest; the rest are "on the way" filler and read smaller.
var TILE_GLYPH = {
  poi: "",        // POI squares show their sequence number instead of a glyph
  easter: "★",    // hidden SR — a small star, still clearly special
  chance: "?",
  photo: "📷",
  street: "·",
};

// CSS class for a board tile marker. `visited` marks squares the pawn has
// already walked so progress is legible (spec §7: "走过的格子要有视觉区分").
function tileClass(tile, visited) {
  var t = (tile && tile.type) || "path";
  var cls = "tile tile-" + t;
  if (visited) cls += " visited";
  return cls;
}

// What the marker shows: a POI shows its 1-based order, everything else a
// small type glyph so the player can tell squares apart at a glance.
function tileText(tile, poiNumber) {
  if (tile && tile.type === "poi") {
    return poiNumber ? String(poiNumber) : "";
  }
  return TILE_GLYPH[(tile && tile.type)] || "";
}

// 1-based ordinal of a POI tile among POI tiles (the Nth stop on the trail).
// Returns 0 for a non-POI tile or an out-of-range index.
function poiOrdinal(board, index) {
  if (!board || index < 0 || index >= board.length) return 0;
  if (board[index].type !== "poi") return 0;
  var n = 0;
  for (var i = 0; i <= index; i++) {
    if (board[i].type === "poi") n += 1;
  }
  return n;
}

// MapLibre wants [lng, lat]; the project stores [lat, lng] everywhere. The
// swap goes through toLngLat so there is one place that knows the convention.
function tileLngLat(tile, toLngLat) {
  return toLngLat([tile.lat, tile.lng]);
}

// Which board tile a played event lands the pawn on. One tiny function, but
// it is the exact thing that had no coverage: the pawn follows e.tileIndex.
function pawnTile(board, event) {
  if (!board || !event) return null;
  var idx = event.tileIndex;
  if (idx === undefined || idx < 0 || idx >= board.length) return null;
  return board[idx];
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { tileClass: tileClass, tileText: tileText,
                     poiOrdinal: poiOrdinal, tileLngLat: tileLngLat,
                     pawnTile: pawnTile, TILE_GLYPH: TILE_GLYPH };
} else if (typeof window !== "undefined") {
  window.LemiBoard = { tileClass: tileClass, tileText: tileText,
                       poiOrdinal: poiOrdinal, tileLngLat: tileLngLat,
                       pawnTile: pawnTile, TILE_GLYPH: TILE_GLYPH };
}
