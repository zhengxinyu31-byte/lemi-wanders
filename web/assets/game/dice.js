// Dice and movement rules.
//
// The die decides HOW FAR Lemi walks, never WHICH tiles she skips: the
// returned path lists every tile passed so the caller can trigger each one.
// A roll past the final tile stops at the end rather than overshooting.

function rollDice(rng) {
  var r = (rng || Math.random)();
  return Math.floor(r * 6) + 1;
}

function resolveMove(from, roll, boardLength) {
  var last = boardLength - 1;
  var to = Math.min(from + roll, last);
  var path = [];
  for (var i = from + 1; i <= to; i++) path.push(i);
  return { to: to, path: path, finished: to >= last };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { rollDice: rollDice, resolveMove: resolveMove };
} else if (typeof window !== "undefined") {
  window.LemiDice = { rollDice: rollDice, resolveMove: resolveMove };
}
