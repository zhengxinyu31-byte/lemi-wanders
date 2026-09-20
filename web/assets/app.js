// Lemi's Diary front-end: load city payload, render storyline stops,
// language switch (single-language display with fallback), MapLibre map.

function pickLang(zh, en, lang) {
  // Single-language display; fall back to the other language if missing.
  if (lang === "en") return en || zh || "";
  return zh || en || "";
}

function visibleForLang(payload, lang) {
  // Shape the payload's active-storyline stops for a given language.
  return (payload.storylines || []).map(function (sl) {
    return {
      id: sl.id,
      title: pickLang(sl.title_zh, sl.title_en, lang),
      stops: (sl.stops || []).map(function (st) {
        return {
          poi_id: st.poi_id, order: st.order,
          narrative: (st.narrative || []).map(function (n) {
            return { type: n.type, text: pickLang(n.text_zh, n.text_en, lang), image: n.image };
          }),
          photo_spot: st.photo_spot
            ? { text: pickLang(st.photo_spot.text_zh, st.photo_spot.text_en, lang), image: st.photo_spot.image }
            : null,
        };
      }),
    };
  });
}

if (typeof window !== "undefined") {
  window.pickLang = pickLang;
  window.visibleForLang = visibleForLang;
  window.LemiApp = { pickLang: pickLang, visibleForLang: visibleForLang };
}

async function boot() {
  const cityId = window.__CITY_ID__ || "paris";
  let lang = localStorage.getItem("lemi_lang") || "zh";
  const payload = await fetch("./data/" + cityId + ".json").then(function (r) { return r.json(); });
  const i18n = await fetch("./i18n/" + lang + ".json").then(function (r) { return r.json(); });

  const map = new maplibregl.Map({
    container: "map",
    style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    center: [payload.city.center_lng, payload.city.center_lat], // MapLibre = [lng,lat]
    zoom: 12,
  });

  let activeStoryline = (payload.storylines[0] || {}).id;

  function render() {
    const shaped = visibleForLang(payload, lang);
    const sl = shaped.find(function (s) { return s.id === activeStoryline; }) || shaped[0];
    // draw route
    const coords = sl.stops.map(function (st) {
      const p = payload.pois[st.poi_id];
      return [p.lng, p.lat];
    });
    if (map.getSource("route")) map.getSource("route").setData(routeGeo(coords));
    else if (map.loaded()) addRoute(map, coords);
    renderStorylineTabs(shaped, sl.id);
    renderSidebar(sl, payload, i18nCurrent, lang);
    addMarkers(map, sl, payload);
  }

  let i18nCurrent = i18n;
  window.__lemiRender = render;
  window.__lemiSwitchLang = async function () {
    lang = lang === "zh" ? "en" : "zh";
    localStorage.setItem("lemi_lang", lang);
    i18nCurrent = await fetch("./i18n/" + lang + ".json").then(function (r) { return r.json(); });
    render();
  };
  window.__lemiSetStoryline = function (id) { activeStoryline = id; render(); };

  map.on("load", render);
}

function routeGeo(coords) {
  return { type: "Feature", geometry: { type: "LineString", coordinates: coords } };
}
function addRoute(map, coords) {
  map.addSource("route", { type: "geojson", data: routeGeo(coords) });
  map.addLayer({ id: "route", type: "line", source: "route",
    paint: { "line-color": "#c0392b", "line-width": 3, "line-dasharray": [2, 1.5] } });
}
function addMarkers(map, sl, payload) {
  (window.__lemiMarkers || []).forEach(function (m) { m.remove(); });
  window.__lemiMarkers = [];
  sl.stops.forEach(function (st) {
    const p = payload.pois[st.poi_id];
    const el = document.createElement("div");
    el.className = "marker"; el.textContent = st.order;
    const m = new maplibregl.Marker({ element: el }).setLngLat([p.lng, p.lat]).addTo(map);
    window.__lemiMarkers.push(m);
  });
}
function renderStorylineTabs(shaped, activeId) {
  const box = document.getElementById("storyline-tabs");
  if (!box) return;
  box.innerHTML = "";
  shaped.forEach(function (sl) {
    const btn = document.createElement("button");
    btn.textContent = sl.title;
    if (sl.id === activeId) {
      btn.style.background = "#c0392b";
      btn.style.color = "#fff";
    }
    btn.addEventListener("click", function () { window.__lemiSetStoryline(sl.id); });
    box.appendChild(btn);
  });
}
function renderSidebar(sl, payload, i18n, lang) {
  const box = document.getElementById("sidebar-content");
  if (!box) return;
  box.innerHTML = "";
  sl.stops.forEach(function (st) {
    const p = payload.pois[st.poi_id];
    const card = document.createElement("div");
    card.className = "poi-card";
    let html = "<h3>" + st.order + ". " + pickLang(p.name_zh, p.name_en, lang) + "</h3>";
    if (p.base_images && p.base_images[0]) {
      html += '<img src="' + p.base_images[0].thumb + '" alt="" />';
    }
    st.narrative.forEach(function (n) {
      html += '<p><b>' + (i18n[n.type] || n.type) + '</b>: ' + n.text + '</p>';
      if (n.image) html += '<img src="' + n.image.thumb + '" alt="" />';
    });
    if (st.photo_spot) html += '<p><b>' + i18n.photo_spot + '</b>: ' + st.photo_spot.text + '</p>';
    if (p.practical) {
      html += '<p><b>' + i18n.practical + '</b>: ' + pickLang(p.practical.text_zh, p.practical.text_en, lang) + '</p>';
    }
    card.innerHTML = html;
    box.appendChild(card);
  });
}

if (typeof document !== "undefined" && document.getElementById) {
  window.addEventListener("DOMContentLoaded", boot);
}
