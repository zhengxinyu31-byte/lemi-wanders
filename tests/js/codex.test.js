const { test } = require("node:test");
const assert = require("node:assert");
const { buildChapters, hashForStop, stopFromHash } =
  require("../../web/assets/codex/codex.js");

const PAYLOAD = {
  night_from_index: 13,
  pois: {
    a: { id: "a", name_zh: "甲", name_en: "A", lat: 1, lng: 2, base_images: [] },
    b: { id: "b", name_zh: "乙", name_en: "B", lat: 3, lng: 4, base_images: [] },
  },
  storylines: [{
    id: "sl", title_zh: "线", title_en: "Line",
    stops: [
      { poi_id: "a", order: 1, narrative: [
        { type: "scene", text_zh: "场景", text_en: "scene" }] },
      { poi_id: "b", order: 2, narrative: [
        { type: "history", text_zh: "历史", text_en: "history" }] },
    ],
  }],
};

test("chapters follow stop order", () => {
  const ch = buildChapters(PAYLOAD, "zh");
  assert.deepStrictEqual(ch.map((c) => c.title), ["甲", "乙"]);
});

test("chapters carry coordinates for the camera", () => {
  assert.deepStrictEqual(buildChapters(PAYLOAD, "zh")[0].center, [2, 1]);
});

test("chapters switch language", () => {
  assert.strictEqual(buildChapters(PAYLOAD, "en")[0].title, "A");
  assert.strictEqual(buildChapters(PAYLOAD, "en")[0].blocks[0].text, "scene");
});

test("hash round-trips a stop number", () => {
  assert.strictEqual(hashForStop(3), "#stop=3");
  assert.strictEqual(stopFromHash("#stop=3"), 3);
});

test("a malformed hash yields the first stop", () => {
  assert.strictEqual(stopFromHash("#nonsense"), 1);
  assert.strictEqual(stopFromHash(""), 1);
  assert.strictEqual(stopFromHash("#stop=abc"), 1);
});

test("codex never reads player state", () => {
  const src = require("fs").readFileSync(
    require("path").join(__dirname, "../../web/assets/codex/codex.js"), "utf8");
  assert.ok(!/lemi_state/.test(src), "codex must not touch player state");
  assert.ok(!/hasCard|cardCount|addCard/.test(src),
            "codex must not read the album");
});
