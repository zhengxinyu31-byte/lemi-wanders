// The card album. Uncollected cards keep a silhouette slot so the player
// can see what is still missing — that visible gap is what drives
// collection. SSR is a city-level reward and never counts toward the
// per-storyline denominator.

var RARITY_ORDER = { R: 0, SR: 1 };

function pick(zh, en, lang) {
  if (lang === "en") return en || zh || "";
  return zh || en || "";
}

function buildCollection(payload, storage, lang) {
  var cards = payload.cards || {};
  var ids = Object.keys(cards).filter(function (id) {
    return cards[id].rarity === "R" || cards[id].rarity === "SR";
  });
  ids.sort(function (a, b) {
    var d = RARITY_ORDER[cards[a].rarity] - RARITY_ORDER[cards[b].rarity];
    return d !== 0 ? d : (a < b ? -1 : 1);
  });

  var owned = 0;
  var slots = ids.map(function (id) {
    var has = storage.hasCard(id);
    if (has) owned += 1;
    return {
      id: id,
      rarity: cards[id].rarity,
      owned: has,
      title: has ? pick(cards[id].title_zh, cards[id].title_en, lang) : "",
    };
  });

  var shards = (storage.load().ssr_shards || {}).paris || 0;
  var required = payload.ssr_shards_required || 3;
  return {
    slots: slots,
    owned: owned,
    total: slots.length,
    ssr: { locked: shards < required, shards: shards, required: required },
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { buildCollection: buildCollection };
} else if (typeof window !== "undefined") {
  window.LemiCollection = { buildCollection: buildCollection };
}
