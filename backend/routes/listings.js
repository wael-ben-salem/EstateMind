const router = require("express").Router();
const c = require("../controllers/listingsController");

router.get("/",             c.list);
router.get("/export",       c.exportCsv);
router.get("/villes",       c.villes);
router.get("/:id/similar",  c.similar);
router.get("/:id/score",    c.score);
router.get("/:id",          c.detail);

module.exports = router;
