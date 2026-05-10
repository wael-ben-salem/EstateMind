const { Database } = require("node-sqlite3-wasm");
const path = require("path");
require("dotenv").config();

const dbPath = path.resolve(process.env.DB_PATH || "../data/estatamind.db");

let db;
function getDb() {
  if (!db) {
    db = new Database(dbPath);
    db.exec("PRAGMA busy_timeout = 5000");
  }
  return db;
}

module.exports = { getDb };
