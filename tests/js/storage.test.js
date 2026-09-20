const { test } = require("node:test");
const assert = require("node:assert");
const { createStorage, CURRENT_VERSION } = require("../../web/assets/core/storage.js");

function memoryBackend(initial) {
  let store = initial === undefined ? {} : initial;
  return {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    _dump: () => store,
  };
}

function brokenBackend() {
  return {
    getItem: () => { throw new Error("SecurityError"); },
    setItem: () => { throw new Error("QuotaExceededError"); },
  };
}

test("fresh state has empty cards and current version", () => {
  const s = createStorage(memoryBackend());
  const st = s.load();
  assert.strictEqual(st.v, CURRENT_VERSION);
  assert.deepStrictEqual(st.cards, []);
});

test("addCard persists across reload", () => {
  const backend = memoryBackend();
  const a = createStorage(backend);
  a.addCard("paris-tour-eiffel-r");
  const b = createStorage(backend);
  assert.ok(b.hasCard("paris-tour-eiffel-r"));
  assert.strictEqual(b.cardCount(), 1);
});

test("addCard is idempotent - replaying a card does not double count", () => {
  const s = createStorage(memoryBackend());
  s.addCard("c1");
  s.addCard("c1");
  s.addCard("c1");
  assert.strictEqual(s.cardCount(), 1);
});

test("addCard reports whether the card was new", () => {
  const s = createStorage(memoryBackend());
  assert.strictEqual(s.addCard("c1"), true);
  assert.strictEqual(s.addCard("c1"), false);
});

test("game still works when localStorage throws", () => {
  const s = createStorage(brokenBackend());
  assert.doesNotThrow(() => s.addCard("c1"));
  assert.strictEqual(s.hasCard("c1"), true);   // 内存里仍然生效
  assert.strictEqual(s.cardCount(), 1);
});

test("corrupt JSON falls back to a fresh state instead of crashing", () => {
  const s = createStorage(memoryBackend({ lemi_state: "{not json" }));
  assert.deepStrictEqual(s.load().cards, []);
});

test("migrate keeps collected cards when version is older", () => {
  const old = JSON.stringify({ v: 0, cards: ["c1", "c2"] });
  const s = createStorage(memoryBackend({ lemi_state: old }));
  const st = s.load();
  assert.strictEqual(st.v, CURRENT_VERSION);
  assert.deepStrictEqual(st.cards, ["c1", "c2"]);  // 绝不能清空
});

test("migrate fills in missing fields from an older shape", () => {
  const old = JSON.stringify({ v: 0, cards: ["c1"] });
  const s = createStorage(memoryBackend({ lemi_state: old }));
  const st = s.load();
  assert.deepStrictEqual(st.storylines, {});
  assert.deepStrictEqual(st.ssr_shards, {});
});

test("setTile records progress per storyline", () => {
  const s = createStorage(memoryBackend());
  s.setTile("emily-in-paris", 7);
  assert.strictEqual(s.load().storylines["emily-in-paris"].tile, 7);
});
