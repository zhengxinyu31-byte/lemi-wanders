const { test } = require("node:test");
const assert = require("node:assert");
const { buildCollection } = require("../../web/assets/game/collection.js");
const { createStorage } = require("../../web/assets/core/storage.js");

function mem() {
  let s = {};
  return { getItem: (k) => (k in s ? s[k] : null),
           setItem: (k, v) => { s[k] = String(v); } };
}

function payloadWith(n) {
  const cards = {};
  for (let i = 0; i < n; i++) {
    cards["c" + i] = { id: "c" + i, rarity: i < 7 ? "R" : "SR",
                       title_zh: "卡" + i, title_en: "Card " + i,
                       body_zh: "正文", body_en: "body" };
  }
  return { cards: cards, ssr_shards_required: 3 };
}

test("every card has a slot even when nothing is collected", () => {
  const c = buildCollection(payloadWith(10), createStorage(mem()), "zh");
  assert.strictEqual(c.slots.length, 10);
  assert.strictEqual(c.owned, 0);
  assert.strictEqual(c.total, 10);
});

test("uncollected slots are silhouettes carrying no title", () => {
  const c = buildCollection(payloadWith(10), createStorage(mem()), "zh");
  assert.strictEqual(c.slots[0].owned, false);
  assert.strictEqual(c.slots[0].title, "");     // 剪影不剧透内容
  assert.strictEqual(c.slots[0].rarity, "R");   // 但稀有度可见
});

test("collected slots reveal their title", () => {
  const st = createStorage(mem());
  st.addCard("c0");
  const c = buildCollection(payloadWith(10), st, "zh");
  assert.strictEqual(c.slots[0].owned, true);
  assert.strictEqual(c.slots[0].title, "卡0");
  assert.strictEqual(c.owned, 1);
});

test("slots are ordered R first then SR", () => {
  const c = buildCollection(payloadWith(10), createStorage(mem()), "zh");
  assert.deepStrictEqual(c.slots.slice(0, 7).map((s) => s.rarity),
                         ["R", "R", "R", "R", "R", "R", "R"]);
  assert.deepStrictEqual(c.slots.slice(7).map((s) => s.rarity),
                         ["SR", "SR", "SR"]);
});

test("ssr is locked and excluded from the denominator", () => {
  const c = buildCollection(payloadWith(10), createStorage(mem()), "zh");
  assert.strictEqual(c.total, 10);          // 不是 11
  assert.strictEqual(c.ssr.locked, true);
  assert.strictEqual(c.ssr.shards, 0);
  assert.strictEqual(c.ssr.required, 3);
});

test("collecting every card does not unlock ssr on its own", () => {
  const st = createStorage(mem());
  for (let i = 0; i < 10; i++) st.addCard("c" + i);
  const c = buildCollection(payloadWith(10), st, "zh");
  assert.strictEqual(c.owned, 10);
  assert.strictEqual(c.ssr.locked, true);   // 需 3 条故事线,非集满本线
});
