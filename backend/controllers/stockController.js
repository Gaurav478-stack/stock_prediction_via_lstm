const axios = require('axios');

class StockController {
  async getStockQuote(req, res) {
    try {
      const { symbol } = req.params;
      const response = await axios.get('https://www.alphavantage.co/query', {
        params: {
          function: 'GLOBAL_QUOTE',
          symbol: symbol.toUpperCase(),
          apikey: process.env.ALPHA_VANTAGE_API_KEY
        }
      });

      if (response.data['Global Quote']) {
        const quote = response.data['Global Quote'];
        const formattedQuote = {
          symbol: quote['01. symbol'],
          price: parseFloat(quote['05. price']),
          change: parseFloat(quote['09. change']),
          changePercent: parseFloat(quote['10. change percent'].replace('%', ''))
        };
        res.json(formattedQuote);
      } else {
        res.status(404).json({ error: 'Stock not found' });
      }
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch stock data' });
    }
  }

  async getTimeSeries(req, res) {
    try {
      const { symbol } = req.params;
      const { interval = 'daily' } = req.query;

      const functionMap = {
        'daily': 'TIME_SERIES_DAILY',
        'weekly': 'TIME_SERIES_WEEKLY',
        'monthly': 'TIME_SERIES_MONTHLY'
      };

      const response = await axios.get('https://www.alphavantage.co/query', {
        params: {
          function: functionMap[interval],
          symbol: symbol.toUpperCase(),
          apikey: process.env.ALPHA_VANTAGE_API_KEY
        }
      });

      const timeSeriesKey = {
        'TIME_SERIES_DAILY': 'Time Series (Daily)',
        'TIME_SERIES_WEEKLY': 'Weekly Time Series',
        'TIME_SERIES_MONTHLY': 'Monthly Time Series'
      }[functionMap[interval]];

      if (response.data[timeSeriesKey]) {
        const timeSeries = response.data[timeSeriesKey];
        const dates = Object.keys(timeSeries).slice(0, 30).reverse();
        
        const formattedData = {
          dates: dates,
          values: dates.map(date => parseFloat(timeSeries[date]['4. close']))
        };
        res.json(formattedData);
      } else {
        res.status(404).json({ error: 'Time series data not found' });
      }
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch time series data' });
    }
  }

  async searchStocks(req, res) {
    try {
      const { query } = req.query;
      
      const response = await axios.get('https://www.alphavantage.co/query', {
        params: {
          function: 'SYMBOL_SEARCH',
          keywords: query,
          apikey: process.env.ALPHA_VANTAGE_API_KEY
        }
      });

      if (response.data['bestMatches']) {
        const results = response.data['bestMatches']
          .map(match => ({
            symbol: match['1. symbol'],
            name: match['2. name']
          }))
          .slice(0, 10);
        res.json(results);
      } else {
        res.json([]);
      }
    } catch (error) {
      res.status(500).json({ error: 'Failed to search stocks' });
    }
  }
}

module.exports = new StockController();