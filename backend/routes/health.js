const router = require("express").Router();
const { getDb } = require("../config/database");

router.get("/", (req, res) => {
  let dbOk = false;
  try { getDb().prepare("SELECT 1").get(); dbOk = true; } catch {}
  res.json({ status: "ok", db: dbOk ? "ok" : "error", uptime: process.uptime(), version: "1.0.0" });
});

module.exports = router;
