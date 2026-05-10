const router = require("express").Router();
const c = require("../controllers/mapController");

router.get("/clusters",             c.clusters);
router.get("/heatmap",              c.heatmap);
router.get("/choropleth",           c.choropleth);
router.get("/time-machine",         c.timeMachine);
router.get("/gouvernerat/:name",    c.gouverneratStats);

module.exports = router;
