const { test } = require("node:test");
const assert = require("node:assert");
const { rollDice, resolveMove } = require("../../web/assets/game/dice.js");

test("rollDice stays within 1..6", () => {
  for (let i = 0; i < 200; i++) {
    const n = rollDice();
    assert.ok(n >= 1 && n <= 6, "got " + n);
    assert.strictEqual(n, Math.floor(n));
  }
});

test("rollDice uses the injected rng", () => {
  assert.strictEqual(rollDice(() => 0), 1);
  assert.strictEqual(rollDice(() => 0.999), 6);
});

test("path lists every tile passed, never skipping one", () => {
  const { to, path } = resolveMove(0, 3, 20);
  assert.strictEqual(to, 3);
  assert.deepStrictEqual(path, [1, 2, 3]);
});

test("move stops at the last tile when the roll overshoots", () => {
  const { to, path, finished } = resolveMove(18, 6, 20);
  assert.strictEqual(to, 19);              // 不得越界到 24
  assert.deepStrictEqual(path, [19]);
  assert.strictEqual(finished, true);
});

test("landing exactly on the last tile finishes the run", () => {
  const { to, finished } = resolveMove(17, 2, 20);
  assert.strictEqual(to, 19);
  assert.strictEqual(finished, true);
});

test("a move that does not reach the end is not finished", () => {
  assert.strictEqual(resolveMove(0, 5, 20).finished, false);
});

test("rolling from the final tile yields an empty path", () => {
  const { to, path, finished } = resolveMove(19, 4, 20);
  assert.strictEqual(to, 19);
  assert.deepStrictEqual(path, []);
  assert.strictEqual(finished, true);
});
