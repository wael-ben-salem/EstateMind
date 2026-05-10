const NodeCache = require("node-cache");

const cache = new NodeCache({
  stdTTL: parseInt(process.env.CACHE_TTL || "300"),
  checkperiod: 60,
  useClones: false,
});

module.exports = cache;
