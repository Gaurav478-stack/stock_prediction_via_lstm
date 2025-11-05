const axios = require('axios');

const ANALYTICS_SERVICE_URL = process.env.ANALYTICS_SERVICE_URL || 'http://localhost:8000';

class AnalyticsController {
  async getAnalysis(req, res) {
    try {
      const { symbol } = req.params;
      const { type = 'technical' } = req.query;

      const response = await axios.get(`${ANALYTICS_SERVICE_URL}/api/analyze/${symbol}`, {
        params: { type }
      });

      res.json(response.data);
    } catch (error) {
      console.error('Analytics service error:', error.message);
      res.status(500).json({ 
        error: 'Failed to fetch analysis',
        message: 'Analytics service may not be running'
      });
    }
  }

  async optimizePortfolio(req, res) {
    try {
      const { symbols, risk_tolerance } = req.body;

      if (!symbols || !Array.isArray(symbols) || symbols.length === 0) {
        return res.status(400).json({ error: 'Symbols array is required' });
      }

      const response = await axios.post(`${ANALYTICS_SERVICE_URL}/api/portfolio/optimize`, {
        symbols,
        risk_tolerance: risk_tolerance || 'medium'
      });

      res.json(response.data);
    } catch (error) {
      console.error('Portfolio optimization error:', error.message);
      res.status(500).json({ 
        error: 'Failed to optimize portfolio',
        message: 'Analytics service may not be running'
      });
    }
  }
}

module.exports = new AnalyticsController();