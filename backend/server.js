require("dotenv").config();
const express  = require("express");
const http     = require("http");
const { Server } = require("socket.io");
const cors     = require("cors");
const helmet   = require("helmet");
const morgan   = require("morgan");
const fs       = require("fs");
const path     = require("path");

const rateLimiter  = require("./middleware/rateLimiter");
const errorHandler = require("./middleware/errorHandler");
const socket       = require("./services/socketService");

const statsRoute    = require("./routes/stats");
const listingsRoute = require("./routes/listings");
const mapRoute      = require("./routes/map");
const pipelineRoute = require("./routes/pipeline");
const healthRoute   = require("./routes/health");

const DB_PATH = path.resolve(process.env.DB_PATH || "../data/estatamind.db");
if (!fs.existsSync(DB_PATH)) {
  console.error(`\n[ERROR] SQLite DB not found at ${DB_PATH}`);
  console.error("  Run: python backend/import_data.py\n");
  process.exit(1);
}

const app    = express();
const server = http.createServer(app);
const io     = new Server(server, { cors: { origin: "*" } });

socket.init(io);

app.use(helmet({ contentSecurityPolicy: false }));
app.use(cors({ origin: process.env.CORS_ORIGIN || "*" }));
app.use(morgan("dev"));
app.use(express.json());
app.use(rateLimiter);

app.use("/api/health",    healthRoute);
app.use("/api/stats",     statsRoute);
app.use("/api/listings",  listingsRoute);
app.use("/api/map",       mapRoute);
app.use("/api/pipeline",  pipelineRoute);

app.use(errorHandler);

io.on("connection", (sock) => {
  sock.on("pipeline:subscribe",   () => sock.join("pipeline"));
  sock.on("pipeline:unsubscribe", () => sock.leave("pipeline"));
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => console.log(`EstataMind API → http://localhost:${PORT}/api/health`));
