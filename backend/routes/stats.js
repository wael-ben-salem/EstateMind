const router = require("express").Router();
const c = require("../controllers/statsController");

router.get("/overview",            c.overview);
router.get("/by-gouvernerat",      c.byGouvernerat);
router.get("/by-type",             c.byType);
router.get("/by-contrat",          c.byContrat);
router.get("/price-distribution",  c.priceDistribution);
router.get("/monthly-trend",       c.monthlyTrend);
router.get("/amenities",           c.amenities);
router.get("/price-heatmap",       c.priceHeatmap);
router.get("/standing-distribution", c.standingDistribution);
router.get("/insights",            c.insights);
router.get("/etrei",               c.etrei);

module.exports = router;
