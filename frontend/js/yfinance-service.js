class YFinanceService {
    constructor() {
        this.baseUrl = CONFIG.BACKEND.ANALYTICS_URL;
    }

    async getQuote(symbol) {
        try {
            console.log(`Fetching quote for ${symbol} using yfinance...`);
            const response = await fetch(`${this.baseUrl}/stock/quote/${symbol}`);
            
            if (response.status === 429) {
                console.warn(`Rate limit hit for ${symbol}, using cached data if available`);
                throw new Error('RATE_LIMIT');
            }
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Log if response was cached
            const cacheStatus = response.headers.get('X-Cache');
            if (cacheStatus === 'HIT') {
                console.log(`✓ Cached response for ${symbol}`);
            } else {
                console.log(`Successfully fetched ${symbol}:`, data);
            }
            
            return {
                symbol: data.symbol,
                name: data.name,
                open: data.open,
                high: data.high,
                low: data.low,
                price: data.price,
                volume: data.volume,
                change: data.change,
                changePercent: data.changePercent,
                previousClose: data.previousClose,
                marketCap: data.marketCap,
                currency: data.currency
            };
        } catch (error) {
            console.error(`Error fetching quote for ${symbol}:`, error);
            throw error;
        }
    }

    async getTimeSeries(symbol, period = '1mo') {
        try {
            console.log(`Fetching time series for ${symbol} using yfinance...`);
            
            // Convert period format
            const periodMap = {
                'TIME_SERIES_DAILY': '1mo',
                'TIME_SERIES_WEEKLY': '3mo',
                'TIME_SERIES_MONTHLY': '1y',
                'daily': '1mo',
                'weekly': '3mo',
                'monthly': '1y'
            };
            
            const apiPeriod = periodMap[period] || period;
            
            const response = await fetch(`${this.baseUrl}/stock/historical/${symbol}?period=${apiPeriod}&interval=1d`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log(`Successfully fetched time series for ${symbol}`);
            
            return {
                dates: data.dates,
                values: data.close
            };
        } catch (error) {
            console.error(`Error fetching time series for ${symbol}:`, error);
            throw error;
        }
    }

    async searchStocks(query) {
        try {
            console.log(`Searching for: ${query}`);
            const response = await fetch(`${this.baseUrl}/stock/search?query=${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data.results || [];
        } catch (error) {
            console.error('Error searching stocks:', error);
            return [];
        }
    }
}

const yfinanceService = new YFinanceService();
