const axios = require('axios');

const ALPHA_VANTAGE_API_KEY = 'RHM3BPM80BKAPFL3';
const BASE_URL = 'https://www.alphavantage.co/query';

class AlphaVantageService {
  constructor() {
    this.apiKey = ALPHA_VANTAGE_API_KEY;
    this.baseUrl = BASE_URL;
  }

  async getQuote(symbol) {
    try {
      const response = await axios.get(this.baseUrl, {
        params: {
          function: 'GLOBAL_QUOTE',
          symbol: symbol,
          apikey: this.apiKey
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching quote:', error.message);
      throw error;
    }
  }

  async getTimeSeries(symbol, interval = 'TIME_SERIES_DAILY') {
    try {
      const response = await axios.get(this.baseUrl, {
        params: {
          function: interval,
          symbol: symbol,
          apikey: this.apiKey,
          outputsize: 'compact'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching time series:', error.message);
      throw error;
    }
  }

  async searchSymbol(keywords) {
    try {
      const response = await axios.get(this.baseUrl, {
        params: {
          function: 'SYMBOL_SEARCH',
          keywords: keywords,
          apikey: this.apiKey
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error searching symbol:', error.message);
      throw error;
    }
  }

  async getCompanyOverview(symbol) {
    try {
      const response = await axios.get(this.baseUrl, {
        params: {
          function: 'OVERVIEW',
          symbol: symbol,
          apikey: this.apiKey
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching company overview:', error.message);
      throw error;
    }
  }
}

module.exports = new AlphaVantageService();
