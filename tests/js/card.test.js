const { test } = require("node:test");
const assert = require("node:assert");
const { shapeCard, rarityClass } = require("../../web/assets/game/card.js");

const RAW = {
  id: "paris-tour-eiffel-r", rarity: "R", poi_id: "tour-eiffel",
  title_zh: "埃菲尔铁塔", title_en: "Eiffel Tower",
  body_zh: "中文正文", body_en: "English body",
  image: { url: "https://x/a.jpg", thumb: "https://x/t.jpg" },
  quote: { text_zh: "译文", text_original: "orig",
           source: "书, 1890", source_url: "https://a.example" },
};

test("shapeCard picks the requested language", () => {
  assert.strictEqual(shapeCard(RAW, "zh").title, "埃菲尔铁塔");
  assert.strictEqual(shapeCard(RAW, "en").title, "Eiffel Tower");
});

test("shapeCard falls back when a translation is missing", () => {
  const partial = Object.assign({}, RAW, { title_en: "" });
  assert.strictEqual(shapeCard(partial, "en").title, "埃菲尔铁塔");
});

test("card without an image is still readable", () => {
  const noImg = Object.assign({}, RAW, { image: null });
  const c = shapeCard(noImg, "zh");
  assert.strictEqual(c.hasImage, false);
  assert.strictEqual(c.body, "中文正文");   // 正文仍在,不是空白卡
  assert.strictEqual(c.title, "埃菲尔铁塔");
});

test("card with a blank image url counts as having no image", () => {
  const blank = Object.assign({}, RAW, { image: { url: "", thumb: "" } });
  assert.strictEqual(shapeCard(blank, "zh").hasImage, false);
});

test("quote is shaped with its source for attribution", () => {
  const q = shapeCard(RAW, "zh").quote;
  assert.strictEqual(q.text, "译文");
  assert.strictEqual(q.original, "orig");
  assert.strictEqual(q.source, "书, 1890");
});

test("card without a quote yields null, not an empty object", () => {
  const noQuote = Object.assign({}, RAW, { quote: undefined });
  assert.strictEqual(shapeCard(noQuote, "zh").quote, null);
});

test("rarityClass maps each rarity to its own class", () => {
  assert.strictEqual(rarityClass("R"), "card-r");
  assert.strictEqual(rarityClass("SR"), "card-sr");
  assert.strictEqual(rarityClass("SSR"), "card-ssr");
});

test("unknown rarity degrades to the common class", () => {
  assert.strictEqual(rarityClass("bogus"), "card-r");
});
