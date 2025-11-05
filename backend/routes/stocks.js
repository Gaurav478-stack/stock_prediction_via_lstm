const express = require('express');
const router = express.Router();
const stockController = require('../controllers/stockController');

router.get('/quote/:symbol', stockController.getStockQuote);
router.get('/timeseries/:symbol', stockController.getTimeSeries);
router.get('/search', stockController.searchStocks);

module.exports = router;