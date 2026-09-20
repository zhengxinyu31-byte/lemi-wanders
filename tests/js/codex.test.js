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

// A contiguous board (array position === index, as the pipeline emits) where
// POI "a" sits before night_from_index (day) and POI "b" sits at it (night) —
// the two units codex must not confuse.
const NIGHT_BOARD = [];
for (let i = 0; i < 14; i++) {
  if (i === 0) NIGHT_BOARD.push({ index: 0, type: "poi", poi_id: "a", lat: 1, lng: 2 });
  else if (i === 13) NIGHT_BOARD.push({ index: 13, type: "poi", poi_id: "b", lat: 3, lng: 4 });
  else NIGHT_BOARD.push({ index: i, type: "street", content_id: "s", lat: 0, lng: 0 });
}
const NIGHT_PAYLOAD = Object.assign({}, PAYLOAD, { board: NIGHT_BOARD });

test("chapters follow stop order", () => {
  const ch = buildChapters(PAYLOAD, "zh");
  assert.deepStrictEqual(ch.map((c) => c.title), ["甲", "乙"]);
});

test("chapters carry coordinates for the camera", () => {
  assert.deepStrictEqual(buildChapters(PAYLOAD, "zh")[0].center, [2, 1]);
});

test("daypart follows the POI's BOARD index, not its stop order", () => {
  const ch = buildChapters(NIGHT_PAYLOAD, "zh");
  // POI a is at board index 0 (< 13) → day; POI b is at board index 13 → night.
  assert.strictEqual(ch[0].night, false);
  assert.strictEqual(ch[1].night, true);
});

test("daypart is false when the board or night index is absent", () => {
  // No board → cannot place the stop; must not crash or guess "night".
  assert.strictEqual(buildChapters(PAYLOAD, "zh")[0].night, false);
  assert.strictEqual(buildChapters(PAYLOAD, "zh")[1].night, false);
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
