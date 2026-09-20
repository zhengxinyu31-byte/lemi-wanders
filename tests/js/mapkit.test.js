const { test } = require("node:test");
const assert = require("node:assert");
const { toLngLat, needsPan, flyOptions } = require("../../web/assets/core/mapkit.js");

test("toLngLat swaps stored lat,lng into MapLibre order", () => {
  assert.deepStrictEqual(toLngLat([48.8584, 2.2945]), [2.2945, 48.8584]);
});

test("a point in the middle of the view needs no pan", () => {
  const vp = { width: 1000, height: 800 };
  assert.strictEqual(needsPan({ x: 500, y: 400 }, vp, 0.15), false);
});

test("a point inside the edge margin needs a pan", () => {
  const vp = { width: 1000, height: 800 };
  assert.strictEqual(needsPan({ x: 100, y: 400 }, vp, 0.15), true);  // 左边缘内
  assert.strictEqual(needsPan({ x: 500, y: 60 }, vp, 0.15), true);   // 上边缘内
});

test("a point outside the viewport needs a pan", () => {
  const vp = { width: 1000, height: 800 };
  assert.strictEqual(needsPan({ x: -20, y: 400 }, vp, 0.15), true);
});

test("poi flight is a pitched cinematic move", () => {
  const o = flyOptions({ lat: 48.86, lng: 2.29 }, false);
  assert.deepStrictEqual(o.center, [2.29, 48.86]);
  assert.strictEqual(o.pitch, 50);
  assert.strictEqual(o.essential, true);   // 缺了它 reduced-motion 会跳过动画
});

test("reduced motion keeps essential but drops the pitch and duration", () => {
  const o = flyOptions({ lat: 48.86, lng: 2.29 }, true);
  assert.strictEqual(o.essential, true);
  assert.strictEqual(o.pitch, 0);
  assert.strictEqual(o.duration, 200);
});
