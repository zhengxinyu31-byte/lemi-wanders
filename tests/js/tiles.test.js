const { test } = require("node:test");
const assert = require("node:assert");
const { resolveTile, isNight, DURATIONS } = require("../../web/assets/game/tiles.js");

const PAYLOAD = {
  pois: { "tour-eiffel": { id: "tour-eiffel", name_zh: "埃菲尔铁塔",
                           name_en: "Eiffel Tower",
                           default_photo_spot: { text_zh: "Trocadéro 机位最佳",
                                                 text_en: "Trocadéro has the best spot" } },
          "cafe-de-flore": { id: "cafe-de-flore", name_zh: "花神咖啡",
                             name_en: "Café de Flore" } },
  cards: { "paris-tour-eiffel-r": { id: "paris-tour-eiffel-r", rarity: "R",
                                    poi_id: "tour-eiffel", title_zh: "铁塔",
                                    title_en: "Tower", body_zh: "正文",
                                    body_en: "body" },
           "paris-sr-petition": { id: "paris-sr-petition", rarity: "SR",
                                  title_zh: "47 人", title_en: "The 47",
                                  body_zh: "正文", body_en: "body" } },
  street_cards: { "paris-bonjour": { id: "paris-bonjour", category: "etiquette",
                                     text_zh: "先说 Bonjour",
                                     text_en: "Say Bonjour" } },
  chance: { "paris-eiffel-petition": { id: "paris-eiffel-petition",
                                       question_zh: "多少人签名?",
                                       question_en: "How many signed?",
                                       options_zh: ["7", "47", "300"],
                                       options_en: ["7", "47", "300"],
                                       answer_index: 1,
                                       explain_zh: "47 位。",
                                       explain_en: "Forty-seven." } },
};

test("poi tile drops the matching R card", () => {
  const t = { index: 0, type: "poi", poi_id: "tour-eiffel" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "card");
  assert.strictEqual(r.content.id, "paris-tour-eiffel-r");
  assert.strictEqual(r.durationMs, DURATIONS.card);
});

test("easter tile drops an SR card", () => {
  const t = { index: 4, type: "easter", content_id: "paris-sr-petition" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "card");
  assert.strictEqual(r.content.rarity, "SR");
});

test("street tile returns text at the shared 3s duration", () => {
  const t = { index: 1, type: "street", content_id: "paris-bonjour" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "street");
  assert.strictEqual(r.content.text, "先说 Bonjour");
  assert.strictEqual(r.durationMs, 3000);
});

test("chance tile carries options and the answer index", () => {
  const t = { index: 2, type: "chance", content_id: "paris-eiffel-petition" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "chance");
  assert.strictEqual(r.content.answerIndex, 1);
  assert.deepStrictEqual(r.content.options, ["7", "47", "300"]);
  assert.strictEqual(r.durationMs, 3000);
});

test("chance tile shapes English options when asked", () => {
  const t = { index: 2, type: "chance", content_id: "paris-eiffel-petition" };
  assert.strictEqual(resolveTile(t, PAYLOAD, "en").content.question,
                     "How many signed?");
});

test("a tile whose content is missing degrades to a skip, not a crash", () => {
  const t = { index: 3, type: "street", content_id: "does-not-exist" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "skip");
  assert.strictEqual(r.durationMs, 0);
});

test("poi tile with no matching card degrades to a skip", () => {
  const t = { index: 0, type: "poi", poi_id: "unknown-poi" };
  assert.strictEqual(resolveTile(t, PAYLOAD, "zh").kind, "skip");
});

test("photo tile with a poi is not a skip and carries name + spot text", () => {
  const t = { index: 12, type: "photo", poi_id: "tour-eiffel" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "photo");
  assert.strictEqual(r.content.name, "埃菲尔铁塔");
  assert.strictEqual(r.content.spot, "Trocadéro 机位最佳");
  assert.strictEqual(r.durationMs, 3000);
});

test("photo tile whose poi has no spot still resolves (spot empty, not skip)", () => {
  const t = { index: 4, type: "photo", poi_id: "cafe-de-flore" };
  const r = resolveTile(t, PAYLOAD, "zh");
  assert.strictEqual(r.kind, "photo");
  assert.strictEqual(r.content.name, "花神咖啡");
  assert.strictEqual(r.content.spot, "");
});

test("photo tile with no poi_id degrades to a skip", () => {
  const t = { index: 4, type: "photo" };
  assert.strictEqual(resolveTile(t, PAYLOAD, "zh").kind, "skip");
});

test("isNight flips at the configured index and stays night after", () => {
  assert.strictEqual(isNight(12, 13), false);
  assert.strictEqual(isNight(13, 13), true);
  assert.strictEqual(isNight(19, 13), true);
});
