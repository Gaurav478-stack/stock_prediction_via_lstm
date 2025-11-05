const express = require('express');
const router = express.Router();
const analyticsController = require('../controllers/analyticsController');

router.get('/analyze/:symbol', analyticsController.getAnalysis);
router.post('/portfolio/optimize', analyticsController.optimizePortfolio);

module.exports = router;