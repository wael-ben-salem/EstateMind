const cache = require("../config/cache");

function cached(key, fn) {
  const hit = cache.get(key);
  if (hit !== undefined) return hit;
  const result = fn();
  cache.set(key, result);
  return result;
}

module.exports = { cached };
