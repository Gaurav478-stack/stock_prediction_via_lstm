class AlphaVantageService {
    constructor() {
        this.apiKey = CONFIG.ALPHA_VANTAGE.API_KEY;
        this.baseUrl = CONFIG.ALPHA_VANTAGE.BASE_URL;
        this.lastRequestTime = 0;
    }

    async waitForRateLimit() {
        const now = Date.now();
        const timeSinceLastRequest = now - this.lastRequestTime;
        const minDelay = CONFIG.ALPHA_VANTAGE.RATE_LIMIT_DELAY;

        if (timeSinceLastRequest < minDelay) {
            await new Promise(resolve => setTimeout(resolve, minDelay - timeSinceLastRequest));
        }
        this.lastRequestTime = Date.now();
    }

    async makeRequest(params) {
        await this.waitForRateLimit();

        const urlParams = new URLSearchParams({
            ...params,
            apikey: this.apiKey
        });

        try {
            console.log('Alpha Vantage API request:', params.function, params.symbol || params.keywords);
            const response = await fetch(`${this.baseUrl}?${urlParams}`);
            const data = await response.json();
            
            if (data['Error Message']) {
                throw new Error(data['Error Message']);
            }
            
            if (data['Note']) {
                // Rate limit message from API
                console.warn('Alpha Vantage rate limit:', data['Note']);
                throw new Error('API rate limit reached. Please wait a moment.');
            }
            
            console.log('Alpha Vantage API response received');
            return data;
        } catch (error) {
            console.error('API request failed:', error.message);
            throw error;
        }
    }

    async getQuote(symbol) {
        const data = await this.makeRequest({
            function: 'GLOBAL_QUOTE',
            symbol: symbol.toUpperCase()
        });
        
        console.log(`Raw API response for ${symbol}:`, data);
        
        if (data['Global Quote'] && Object.keys(data['Global Quote']).length > 0) {
            const quote = data['Global Quote'];
            return {
                symbol: quote['01. symbol'] || symbol,
                open: parseFloat(quote['02. open']) || 0,
                high: parseFloat(quote['03. high']) || 0,
                low: parseFloat(quote['04. low']) || 0,
                price: parseFloat(quote['05. price']) || 0,
                volume: parseInt(quote['06. volume']) || 0,
                change: parseFloat(quote['09. change']) || 0,
                changePercent: parseFloat(quote['10. change percent']?.replace('%', '')) || 0
            };
        }
        
        // Check if it's an empty response (common with free tier)
        if (data['Global Quote'] && Object.keys(data['Global Quote']).length === 0) {
            throw new Error(`Empty response - API may be rate limited`);
        }
        
        throw new Error(`No quote data for ${symbol}`);
    }

    async getTimeSeries(symbol, interval = 'daily') {
        const functionMap = {
            'daily': 'TIME_SERIES_DAILY',
            'weekly': 'TIME_SERIES_WEEKLY',
            'monthly': 'TIME_SERIES_MONTHLY'
        };

        const data = await this.makeRequest({
            function: functionMap[interval],
            symbol: symbol.toUpperCase(),
            outputsize: 'compact'
        });
        
        const timeSeriesKey = {
            'TIME_SERIES_DAILY': 'Time Series (Daily)',
            'TIME_SERIES_WEEKLY': 'Weekly Time Series',
            'TIME_SERIES_MONTHLY': 'Monthly Time Series'
        }[functionMap[interval]];

        if (data[timeSeriesKey]) {
            const timeSeries = data[timeSeriesKey];
            const dates = Object.keys(timeSeries).slice(0, 30).reverse();
            
            return {
                dates: dates,
                values: dates.map(date => parseFloat(timeSeries[date]['4. close']))
            };
        }
        
        throw new Error(`No time series data for ${symbol}`);
    }

    async searchStocks(query) {
        const data = await this.makeRequest({
            function: 'SYMBOL_SEARCH',
            keywords: query
        });
        
        if (data['bestMatches']) {
            return data['bestMatches'].map(match => ({
                symbol: match['1. symbol'],
                name: match['2. name'],
                region: match['4. region']
            })).slice(0, 8);
        }
        
        return [];
    }
}

const alphaVantageService = new AlphaVantageService();