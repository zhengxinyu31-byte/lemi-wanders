// Card shaping. A card must stay readable when its image is missing or
// fails to load, so hasImage is reported separately from the text.

function pick(zh, en, lang) {
  if (lang === "en") return en || zh || "";
  return zh || en || "";
}

function shapeCard(raw, lang) {
  var img = raw.image || null;
  var hasImage = !!(img && img.url);
  var quote = null;
  if (raw.quote) {
    quote = {
      text: raw.quote.text_zh || "",
      original: raw.quote.text_original || "",
      source: raw.quote.source || "",
      sourceUrl: raw.quote.source_url || "",
    };
  }
  return {
    id: raw.id,
    rarity: raw.rarity,
    poiId: raw.poi_id || "",
    title: pick(raw.title_zh, raw.title_en, lang),
    body: pick(raw.body_zh, raw.body_en, lang),
    image: img,
    hasImage: hasImage,
    quote: quote,
  };
}

function rarityClass(rarity) {
  if (rarity === "SSR") return "card-ssr";
  if (rarity === "SR") return "card-sr";
  return "card-r";
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { shapeCard: shapeCard, rarityClass: rarityClass };
} else if (typeof window !== "undefined") {
  window.LemiCard = { shapeCard: shapeCard, rarityClass: rarityClass };
}
