// Page wiring for game mode: boot the map, draw the board, bind the die,
// render cards. All decision logic lives in the tested modules (game.js,
// tiles.js, board_view.js, collection.js); this file only moves DOM.

(function () {
  if (typeof window === "undefined" || !document.getElementById) return;

  var B = window.LemiBoard;

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
    // Keyboard users must be able to collect the card too (spec §12): the die
    // stays disabled until the card's Promise resolves, and before this the
    // only way to resolve it was a mouse click — a keyboard user landing on a
    // POI was trapped forever.
    box.setAttribute("tabindex", "0");
    box.setAttribute("role", "button");
    box.setAttribute("aria-label", card.title);
    var collected = false;
    function collect() {
      if (collected) return;   // click + keydown must not double-fire
      collected = true;
      box.remove();
      onClose();
    }
    box.addEventListener("click", collect);
    box.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter" || ev.key === " " || ev.key === "Spacebar") {
        ev.preventDefault();
        collect();
      }
    });
    host.appendChild(box);
    box.focus();
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
    var board = payload.board || [];

    // ---- Board rendering (spec §7). Without this the player sees a bare
    // basemap flying around: no squares, no pawn, no sense of where Lemi is.
    var tileMarkers = [];      // index -> MapLibre Marker for each board tile
    var visited = {};          // index -> true once the pawn has been there
    var pawnMarker = null;

    function markTileVisited(idx) {
      visited[idx] = true;
      var m = tileMarkers[idx];
      if (m) m.getElement().className = B.tileClass(board[idx], true);
    }

    function drawBoard() {
      board.forEach(function (tile, idx) {
        var el = document.createElement("div");
        el.className = B.tileClass(tile, false);
        el.textContent = B.tileText(tile, B.poiOrdinal(board, idx));
        el.setAttribute("aria-hidden", "true");
        var m = new maplibregl.Marker({ element: el })
          .setLngLat(B.tileLngLat(tile, window.LemiMap.toLngLat))
          .addTo(map);
        tileMarkers[idx] = m;
      });
    }

    function drawPawn() {
      var start = game.state().position;
      var tile = board[start];
      if (!tile) return;
      var el = document.createElement("div");
      el.id = "pawn";
      el.textContent = "🐹";          // Lemi: cowboy-hat, camera-toting hamster
      el.setAttribute("role", "img");
      el.setAttribute("aria-label", "Lemi");
      pawnMarker = new maplibregl.Marker({ element: el, anchor: "bottom" })
        .setLngLat(B.tileLngLat(tile, window.LemiMap.toLngLat))
        .addTo(map);
      markTileVisited(start);
    }

    function movePawn(event) {
      var tile = B.pawnTile(board, event);
      if (!tile || !pawnMarker) return;
      // CSS handles the --t-walk glide; setLngLat updates the anchor.
      pawnMarker.setLngLat(B.tileLngLat(tile, window.LemiMap.toLngLat));
      markTileVisited(event.tileIndex);
    }

    function refreshAlbum() {
      var c = window.LemiCollection.buildCollection(payload, storage, lang);
      document.getElementById("album-count").textContent =
        c.owned + "/" + c.total;
    }

    function setDaypart(night) {
      document.body.classList.toggle("night", night);
      document.getElementById("daypart").textContent = night ? "🌃 夜晚" : "☀️ 白天";
    }

    // ---- Album overlay (spec §8). buildCollection already computes the
    // silhouette slots, owned/total and SSR shard progress; this renders it.
    function openAlbum() {
      var c = window.LemiCollection.buildCollection(payload, storage, lang);
      var overlay = document.createElement("div");
      overlay.id = "album";
      overlay.setAttribute("role", "dialog");
      overlay.setAttribute("aria-modal", "true");
      overlay.setAttribute("aria-label", "卡册");

      var head = document.createElement("div");
      head.className = "album-head";
      var count = document.createElement("span");
      count.className = "album-total";
      count.textContent = c.owned + "/" + c.total;
      var close = document.createElement("button");
      close.type = "button";
      close.className = "album-close";
      close.textContent = "✕";
      close.setAttribute("aria-label", "关闭卡册");
      head.appendChild(count);
      head.appendChild(close);
      overlay.appendChild(head);

      var grid = document.createElement("div");
      grid.className = "album-grid";
      c.slots.forEach(function (slot) {
        var cell = document.createElement("div");
        cell.className = "slot" + (slot.owned ? " owned" : " locked");
        if (slot.owned) {
          cell.textContent = slot.title;   // "?" for locked comes from CSS
        }
        grid.appendChild(cell);
      });
      overlay.appendChild(grid);

      // SSR: always a visible locked reward with shard progress (spec §8).
      var ssr = document.createElement("div");
      ssr.className = "ssr-slot" + (c.ssr.locked ? " locked" : " owned");
      ssr.textContent = "SSR " + (c.ssr.locked ? "🔒 " : "") +
        c.ssr.shards + "/" + c.ssr.required;
      overlay.appendChild(ssr);

      function dismiss() {
        overlay.remove();
        document.removeEventListener("keydown", onKey);
      }
      function onKey(ev) { if (ev.key === "Escape") dismiss(); }
      close.addEventListener("click", dismiss);
      overlay.addEventListener("click", function (ev) {
        if (ev.target === overlay) dismiss();   // click backdrop to close
      });
      document.addEventListener("keydown", onKey);

      document.body.appendChild(overlay);
      close.focus();
    }

    async function playEvents(events) {
      for (var i = 0; i < events.length; i++) {
        var e = events[i];
        movePawn(e);
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
          var photoText = e.content.name
            + (e.content.spot ? "<br>" + e.content.spot : "");
          renderInfo("📸", photoText, host);
          await new Promise(function (r) { setTimeout(r, reduced() ? 200 : T.info); });
        }
      }
    }

    document.getElementById("album-btn").addEventListener("click", openAlbum);

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
      drawBoard();
      drawPawn();
      refreshAlbum();
      setDaypart(game.state().night);
      // The board's opening tile (Emily's flat) is never walked by roll(),
      // so its card is only ever collected here. start() is async and
      // idempotent, so it must be awaited and reloading the page is safe.
      await playEvents(await game.start());
    });
  }

  window.addEventListener("DOMContentLoaded", boot);
})();
