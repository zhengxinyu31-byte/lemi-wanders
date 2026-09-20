// MapLibre helpers.
//
// Camera policy, borrowed from storymap: during a walk the camera stays
// put and only pans once the pawn reaches the edge of the view. Constant
// camera motion is what makes map playback nauseating. A pitched flyTo is
// reserved for arriving at a POI, where the move is the point.
//
// Coordinates are stored as [lat, lng] project-wide and only swapped here.

var PITCH_ON_ARRIVAL = 50;
var EDGE_MARGIN = 0.15;

function toLngLat(latLng) {
  return [latLng[1], latLng[0]];
}

function needsPan(point, viewport, marginRatio) {
  var m = marginRatio === undefined ? EDGE_MARGIN : marginRatio;
  var mx = viewport.width * m;
  var my = viewport.height * m;
  return point.x < mx || point.x > viewport.width - mx
      || point.y < my || point.y > viewport.height - my;
}

function flyOptions(tile, reduced) {
  // essential:true is required, or the OS "reduce motion" setting turns
  // this into a jumpTo and the arrival moment disappears.
  if (reduced) {
    return { center: [tile.lng, tile.lat], zoom: 15, pitch: 0,
             duration: 200, essential: true };
  }
  return { center: [tile.lng, tile.lat], zoom: 16,
           pitch: PITCH_ON_ARRIVAL, bearing: -20,
           speed: 0.8, curve: 1.2, essential: true };
}

function prefersReducedMotion() {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function createCamera(map, opts) {
  var reduced = (opts && opts.reduced !== undefined)
    ? opts.reduced : prefersReducedMotion();
  return {
    moveTo: function (tile, isPoi) {
      if (isPoi) {
        map.flyTo(flyOptions(tile, reduced));
        return;
      }
      var p = map.project([tile.lng, tile.lat]);
      var c = map.getContainer();
      if (needsPan(p, { width: c.clientWidth, height: c.clientHeight })) {
        map.panTo([tile.lng, tile.lat], { duration: reduced ? 200 : 600 });
      }
    },
    reduced: reduced,
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { toLngLat: toLngLat, needsPan: needsPan,
                     flyOptions: flyOptions, createCamera: createCamera };
} else if (typeof window !== "undefined") {
  window.LemiMap = { toLngLat: toLngLat, needsPan: needsPan,
                     flyOptions: flyOptions, createCamera: createCamera };
}
