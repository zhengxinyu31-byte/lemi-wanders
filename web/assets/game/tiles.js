// Tile resolution: given a board tile, work out what to show and for how
// long. Missing content degrades to a skip so a content gap never stalls
// the game loop.

var DURATIONS = { card: 600, info: 3000 };

function pick(zh, en, lang) {
  if (lang === "en") return en || zh || "";
  return zh || en || "";
}

function _card(raw, lang) {
  var shape = (typeof require !== "undefined")
    ? require("./card.js").shapeCard
    : window.LemiCard.shapeCard;
  return { kind: "card", durationMs: DURATIONS.card, content: shape(raw, lang) };
}

function _skip() {
  return { kind: "skip", durationMs: 0, content: null };
}

function resolveTile(tile, payload, lang) {
  if (tile.type === "poi") {
    var cards = payload.cards || {};
    for (var id in cards) {
      if (cards[id].poi_id === tile.poi_id) return _card(cards[id], lang);
    }
    return _skip();
  }
  if (tile.type === "easter") {
    var c = (payload.cards || {})[tile.content_id];
    return c ? _card(c, lang) : _skip();
  }
  if (tile.type === "street") {
    var s = (payload.street_cards || {})[tile.content_id];
    if (!s) return _skip();
    return { kind: "street", durationMs: DURATIONS.info,
             content: { id: s.id, category: s.category,
                        text: pick(s.text_zh, s.text_en, lang) } };
  }
  if (tile.type === "chance") {
    var q = (payload.chance || {})[tile.content_id];
    if (!q) return _skip();
    return { kind: "chance", durationMs: DURATIONS.info,
             content: { id: q.id,
                        question: pick(q.question_zh, q.question_en, lang),
                        options: lang === "en" ? q.options_en : q.options_zh,
                        answerIndex: q.answer_index,
                        explain: pick(q.explain_zh, q.explain_en, lang) } };
  }
  if (tile.type === "photo") {
    var poi = (payload.pois || {})[tile.poi_id] || null;
    if (!poi) return _skip();
    return { kind: "photo", durationMs: DURATIONS.info,
             content: { poiId: poi.id,
                        name: pick(poi.name_zh, poi.name_en, lang),
                        image: (poi.base_images || [])[0] || null } };
  }
  return _skip();
}

function isNight(index, nightFrom) {
  return index >= nightFrom;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { resolveTile: resolveTile, isNight: isNight,
                     DURATIONS: DURATIONS };
} else if (typeof window !== "undefined") {
  window.LemiTiles = { resolveTile: resolveTile, isNight: isNight,
                       DURATIONS: DURATIONS };
}
