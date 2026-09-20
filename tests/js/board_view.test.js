const { test } = require("node:test");
const assert = require("node:assert");
const { tileClass, tileText, poiOrdinal, tileLngLat, pawnTile } =
  require("../../web/assets/game/board_view.js");
const { toLngLat } = require("../../web/assets/core/mapkit.js");

const BOARD = [
  { index: 0, type: "poi", poi_id: "a", lat: 48.1, lng: 2.1 },
  { index: 1, type: "street", content_id: "s1", lat: 48.2, lng: 2.2 },
  { index: 2, type: "poi", poi_id: "b", lat: 48.3, lng: 2.3 },
  { index: 3, type: "chance", content_id: "c1", lat: 48.4, lng: 2.4 },
  { index: 4, type: "easter", content_id: "e1", lat: 48.5, lng: 2.5 },
  { index: 5, type: "photo", poi_id: "b", lat: 48.6, lng: 2.6 },
];

test("tileClass encodes type and unvisited state", () => {
  assert.strictEqual(tileClass(BOARD[0], false), "tile tile-poi");
  assert.strictEqual(tileClass(BOARD[1], false), "tile tile-street");
});

test("tileClass adds visited so walked squares are distinguishable", () => {
  assert.strictEqual(tileClass(BOARD[0], true), "tile tile-poi visited");
});

test("tileText shows the POI's 1-based ordinal, not its board index", () => {
  assert.strictEqual(tileText(BOARD[0], poiOrdinal(BOARD, 0)), "1");
  assert.strictEqual(tileText(BOARD[2], poiOrdinal(BOARD, 2)), "2");
});

test("tileText shows a type glyph for non-POI squares", () => {
  assert.strictEqual(tileText(BOARD[1]), "·");   // street
  assert.strictEqual(tileText(BOARD[3]), "?");   // chance
  assert.strictEqual(tileText(BOARD[4]), "★");   // easter
  assert.strictEqual(tileText(BOARD[5]), "📷");  // photo
});

test("poiOrdinal counts only POI tiles up to the index", () => {
  assert.strictEqual(poiOrdinal(BOARD, 0), 1);
  assert.strictEqual(poiOrdinal(BOARD, 2), 2);
});

test("poiOrdinal is 0 for a non-POI tile or out-of-range index", () => {
  assert.strictEqual(poiOrdinal(BOARD, 1), 0);   // street tile
  assert.strictEqual(poiOrdinal(BOARD, 99), 0);
  assert.strictEqual(poiOrdinal(BOARD, -1), 0);
});

test("tileLngLat swaps [lat,lng] to MapLibre's [lng,lat]", () => {
  assert.deepStrictEqual(tileLngLat(BOARD[0], toLngLat), [2.1, 48.1]);
});

test("pawnTile returns the tile named by the event's tileIndex", () => {
  assert.strictEqual(pawnTile(BOARD, { tileIndex: 3 }), BOARD[3]);
  assert.strictEqual(pawnTile(BOARD, { tileIndex: 0 }), BOARD[0]);
});

test("pawnTile is null for a missing or out-of-range tileIndex", () => {
  assert.strictEqual(pawnTile(BOARD, {}), null);
  assert.strictEqual(pawnTile(BOARD, { tileIndex: 99 }), null);
  assert.strictEqual(pawnTile(BOARD, null), null);
});
