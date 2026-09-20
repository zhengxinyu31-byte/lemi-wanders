// Codex mode: a read-only scrollytelling view of a storyline.
//
// This mode deliberately knows nothing about the player: no cards, no
// progress, no localStorage beyond the shared language preference. It
// serves the reader who just wants the material.

function pick(zh, en, lang) {
  if (lang === "en") return en || zh || "";
  return zh || en || "";
}

// The board index of a stop's POI. night_from_index is a BOARD index, so a
// stop's daypart must be judged by where its POI sits on the board — never by
// stop.order (1..7), which is a different unit and made every chapter "day".
function poiBoardIndex(board, poiId) {
  for (var i = 0; i < (board || []).length; i++) {
    if (board[i].type === "poi" && board[i].poi_id === poiId) return i;
  }
  return -1;
}

function buildChapters(payload, lang) {
  var sl = (payload.storylines || [])[0];
  if (!sl) return [];
  var board = payload.board || [];
  var nightFrom = payload.night_from_index;
  var stops = (sl.stops || []).slice().sort(function (a, b) {
    return a.order - b.order;
  });
  return stops.map(function (st) {
    var poi = (payload.pois || {})[st.poi_id] || {};
    var boardIdx = poiBoardIndex(board, st.poi_id);
    return {
      order: st.order,
      poiId: st.poi_id,
      title: pick(poi.name_zh, poi.name_en, lang),
      center: [poi.lng, poi.lat],
      image: (poi.base_images || [])[0] || null,
      night: nightFrom !== undefined && boardIdx >= 0 && boardIdx >= nightFrom,
      blocks: (st.narrative || []).map(function (n) {
        return { type: n.type, text: pick(n.text_zh, n.text_en, lang) };
      }),
    };
  });
}

function hashForStop(n) { return "#stop=" + n; }

function stopFromHash(hash) {
  var m = /^#stop=(\d+)$/.exec(hash || "");
  return m ? parseInt(m[1], 10) : 1;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { buildChapters: buildChapters, hashForStop: hashForStop,
                     stopFromHash: stopFromHash };
} else if (typeof window !== "undefined") {
  window.LemiCodex = { buildChapters: buildChapters, hashForStop: hashForStop,
                       stopFromHash: stopFromHash };
}
