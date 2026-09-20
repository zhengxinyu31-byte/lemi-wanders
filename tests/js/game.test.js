const { test } = require("node:test");
const assert = require("node:assert");
const { createGame } = require("../../web/assets/game/game.js");
const { createStorage } = require("../../web/assets/core/storage.js");

function mem() {
  let s = {};
  return { getItem: (k) => (k in s ? s[k] : null),
           setItem: (k, v) => { s[k] = String(v); } };
}

const PAYLOAD = {
  night_from_index: 3,
  board: [
    { index: 0, type: "poi", lat: 48.84, lng: 2.34, poi_id: "a" },
    { index: 1, type: "street", lat: 48.845, lng: 2.345, content_id: "s1" },
    { index: 2, type: "poi", lat: 48.85, lng: 2.35, poi_id: "b" },
    { index: 3, type: "easter", lat: 48.855, lng: 2.355, content_id: "e1" },
    { index: 4, type: "poi", lat: 48.86, lng: 2.36, poi_id: "c" },
  ],
  pois: { a: { id: "a" }, b: { id: "b" }, c: { id: "c" } },
  cards: {
    ca: { id: "ca", rarity: "R", poi_id: "a", title_zh: "A", title_en: "A",
          body_zh: "x", body_en: "x" },
    cb: { id: "cb", rarity: "R", poi_id: "b", title_zh: "B", title_en: "B",
          body_zh: "x", body_en: "x" },
    cc: { id: "cc", rarity: "R", poi_id: "c", title_zh: "C", title_en: "C",
          body_zh: "x", body_en: "x" },
    e1: { id: "e1", rarity: "SR", title_zh: "E", title_en: "E",
          body_zh: "x", body_en: "x" },
  },
  street_cards: { s1: { id: "s1", category: "rule", text_zh: "街",
                        text_en: "street" } },
  chance: {},
};

function fakeDeps(rollValue) {
  const moves = [];
  return {
    rng: () => (rollValue - 1) / 6 + 0.01,
    camera: { moveTo: (tile, isPoi) => moves.push([tile.index, isPoi]) },
    lang: "zh",
    _moves: moves,
  };
}

test("a roll of 2 from the start passes tile 1 and lands on tile 2", async () => {
  const deps = fakeDeps(2);
  const g = createGame(PAYLOAD, createStorage(mem()), deps);
  const events = await g.roll();
  assert.deepStrictEqual(events.map((e) => e.tileIndex), [1, 2]);
});

test("a POI passed mid-path still fires - the die never skips content", async () => {
  const deps = fakeDeps(4);           // 0 -> 4,途经 1,2,3
  const g = createGame(PAYLOAD, createStorage(mem()), deps);
  const events = await g.roll();
  const poiEvents = events.filter((e) => e.kind === "card" && e.content.rarity === "R");
  assert.ok(poiEvents.some((e) => e.tileIndex === 2), "tile 2 POI must fire");
  assert.strictEqual(events.length, 4);
});

test("landing on a POI marks the card as newly collected", async () => {
  const g = createGame(PAYLOAD, createStorage(mem()), fakeDeps(2));
  const events = await g.roll();
  const card = events.find((e) => e.kind === "card");
  assert.strictEqual(card.isNew, true);
});

test("replaying an owned card reports isNew false and count stays put", async () => {
  const storage = createStorage(mem());
  storage.addCard("cb");
  const g = createGame(PAYLOAD, storage, fakeDeps(2));
  const events = await g.roll();
  const card = events.find((e) => e.kind === "card");
  assert.strictEqual(card.isNew, false);
  assert.strictEqual(storage.cardCount(), 1);
});

test("camera pitches only on POI tiles", async () => {
  const deps = fakeDeps(2);
  const g = createGame(PAYLOAD, createStorage(mem()), deps);
  await g.roll();
  assert.deepStrictEqual(deps._moves, [[1, false], [2, true]]);
});

test("crossing the night index flags the event", async () => {
  const g = createGame(PAYLOAD, createStorage(mem()), fakeDeps(4));
  const events = await g.roll();
  assert.strictEqual(events.find((e) => e.tileIndex === 2).night, false);
  assert.strictEqual(events.find((e) => e.tileIndex === 3).night, true);
});

test("reaching the last tile finishes the run", async () => {
  const g = createGame(PAYLOAD, createStorage(mem()), fakeDeps(6));
  const events = await g.roll();
  assert.strictEqual(events[events.length - 1].finished, true);
  assert.strictEqual(g.state().position, 4);
});

test("rolling after the run finished yields no events", async () => {
  const g = createGame(PAYLOAD, createStorage(mem()), fakeDeps(6));
  await g.roll();
  assert.deepStrictEqual(await g.roll(), []);
});

test("position survives a reload through storage", async () => {
  const backend = mem();
  const g = createGame(PAYLOAD, createStorage(backend), fakeDeps(2));
  await g.roll();
  const g2 = createGame(PAYLOAD, createStorage(backend), fakeDeps(1));
  assert.strictEqual(g2.state().position, 2);
});
