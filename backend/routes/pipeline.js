const router = require("express").Router();
const c = require("../controllers/pipelineController");

router.get("/status",        c.status);
router.post("/trigger",      c.trigger);
router.get("/runs",          c.runs);
router.get("/run/:id/tasks", c.runTasks);
router.get("/quality",       c.quality);

module.exports = router;
