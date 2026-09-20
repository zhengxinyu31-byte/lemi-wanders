// Page wiring for game mode: boot the map, bind the die, render cards.
// All decision logic lives in the tested modules; this file only moves DOM.

(function () {
  if (typeof window === "undefined" || !document.getElementById) return;

  var T = { press: 100, dice: 400, walk: 1000, cardOut: 150,
            develop: 350, set: 100, info: 3000 };

  function reduced() {
    return window.matchMedia
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function toast(msg) {
    var el = document.getElementById("toast");
    el.textContent = msg;
    el.classList.add("show");
    setTimeout(function () { el.classList.remove("show"); }, 1600);
  }

  function renderCard(card, host, onClose) {
    var box = document.createElement("div");
    box.className = "card " + window.LemiCard.rarityClass(card.rarity);
    var html = "";
    if (card.hasImage) {
      html += '<img src="' + card.image.thumb + '" alt="" '
            + 'onerror="this.style.display=\'none\'" />';
    }
    html += "<h3>" + card.title + "</h3>";
    html += '<p class="serif">' + card.body + "</p>";
    if (card.quote) {
      html += '<p class="quote handwriting">「' + card.quote.text + "」</p>";
      html += '<p class="source">' + card.quote.source + "</p>";
    }
    box.innerHTML = html;
    // Any click anywhere collects the card — no extra button to aim at.
    box.addEventListener("click", function () { box.remove(); onClose(); });
    host.appendChild(box);
    if (!reduced()) {
      setTimeout(function () { box.classList.add("set"); }, T.develop);
    }
  }

  function renderInfo(title, text, host) {
    var box = document.createElement("div");
    box.className = "card card-r";
    box.innerHTML = "<h3>" + title + '</h3><p class="serif">' + text + "</p>";
    host.appendChild(box);
    setTimeout(function () { box.remove(); }, reduced() ? 200 : T.info);
  }

  async function boot() {
    var cityId = window.__CITY_ID__ || "paris";
    var lang = localStorage.getItem("lemi_lang") || "zh";
    var payload = await fetch("./data/" + cityId + ".json").then(function (r) {
      return r.json();
    });

    var map = new maplibregl.Map({
      container: "map",
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: [payload.city.center_lng, payload.city.center_lat],
      zoom: 13,
    });

    var storage = window.LemiStorage.createStorage(window.localStorage);
    var camera = window.LemiMap.createCamera(map);
    var game = window.LemiGame.createGame(payload, storage,
                                          { camera: camera, lang: lang });
    var host = document.getElementById("card-host");

    function refreshAlbum() {
      var c = window.LemiCollection.buildCollection(payload, storage, lang);
      document.getElementById("album-count").textContent =
        c.owned + "/" + c.total;
    }

    function setDaypart(night) {
      document.body.classList.toggle("night", night);
      document.getElementById("daypart").textContent = night ? "🌃 夜晚" : "☀️ 白天";
    }

    async function playEvents(events) {
      for (var i = 0; i < events.length; i++) {
        var e = events[i];
        setDaypart(e.night);
        if (e.kind === "card") {
          await new Promise(function (done) {
            renderCard(e.content, host, function () {
              if (e.isNew) { refreshAlbum(); toast("已收入卡册"); }
              done();
            });
          });
        } else if (e.kind === "street") {
          renderInfo("🗺️", e.content.text, host);
          await new Promise(function (r) { setTimeout(r, reduced() ? 200 : T.info); });
        } else if (e.kind === "chance") {
          renderInfo("🎴", e.content.question + "<br><b>"
                     + e.content.options[e.content.answerIndex] + "</b><br>"
                     + e.content.explain, host);
          await new Promise(function (r) { setTimeout(r, reduced() ? 200 : T.info); });
        } else if (e.kind === "photo") {
          renderInfo("📸", e.content.name, host);
          await new Promise(function (r) { setTimeout(r, reduced() ? 200 : T.info); });
        }
      }
    }

    var dice = document.getElementById("dice");
    dice.addEventListener("click", async function () {
      if (dice.disabled) return;
      dice.disabled = true;
      dice.classList.add("rolling");
      await new Promise(function (r) { setTimeout(r, reduced() ? 0 : T.dice); });
      dice.classList.remove("rolling");
      await playEvents(await game.roll());
      dice.disabled = false;
    });

    map.on("load", async function () {
      refreshAlbum();
      setDaypart(game.state().night);
      // The board's opening tile (Emily's flat) is never walked by roll(),
      // so its card is only ever collected here. start() is idempotent, so
      // reloading the page is safe.
      await playEvents(game.start());
    });
  }

  window.addEventListener("DOMContentLoaded", boot);
})();
