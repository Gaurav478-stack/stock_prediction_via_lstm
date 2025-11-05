class DataService {
    constructor() {
        this.cache = new Map();
    }

    setCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    getCache(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < CONFIG.APP.CACHE_DURATION) {
            return cached.data;
        }
        return null;
    }

    async getStockData(symbol) {
        const cacheKey = `stock_${symbol}`;
        const cached = this.getCache(cacheKey);
        if (cached) return cached;

        try {
            // Use yfinance service (unlimited!) instead of Alpha Vantage
            const data = await yfinanceService.getQuote(symbol);
            this.setCache(cacheKey, data);
            return data;
        } catch (error) {
            console.error(`Error fetching ${symbol}:`, error);
            throw error;
        }
    }

    async getWatchlistData(symbols) {
        try {
            console.log('Fetching watchlist data for:', symbols);
            const promises = symbols.map(symbol => 
                this.getStockData(symbol).catch(err => {
                    console.warn(`Failed to fetch ${symbol}:`, err.message);
                    return null;
                })
            );
            const results = await Promise.all(promises);
            const validResults = results.filter(stock => stock !== null);
            console.log(`Successfully fetched ${validResults.length} of ${symbols.length} stocks`);
            return validResults;
        } catch (error) {
            console.error('Error fetching watchlist:', error);
            return [];
        }
    }

    async getMarketData() {
        try {
            const spyData = await yfinanceService.getTimeSeries('SPY', '1mo');
            return {
                chartData: spyData
            };
        } catch (error) {
            console.error('Error fetching market data:', error);
            return this.getDefaultMarketData();
        }
    }

    async getStockDetail(symbol) {
        try {
            const [quote, timeSeries] = await Promise.all([
                this.getStockData(symbol),
                yfinanceService.getTimeSeries(symbol, '1mo')
            ]);
            return { quote, timeSeries };
        } catch (error) {
            console.error(`Error fetching stock detail for ${symbol}:`, error);
            throw error;
        }
    }

    async getAIAnalysis(symbol, analysisType = 'technical') {
        if (!CONFIG.FEATURES.ENABLE_PYTHON_ANALYTICS) {
            throw new Error('Analytics service is disabled');
        }

        try {
            const response = await fetch(
                `${CONFIG.BACKEND.ANALYTICS_URL}/analyze/${symbol}?type=${analysisType}`
            );
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('AI analysis failed:', error);
            throw error; // Don't use mock data
        }
    }

    getDefaultMarketData() {
        return {
            sentiment: 50,
            chartData: { labels: [], values: [] }
        };
    }

    formatPrice(price, currency = 'USD', symbol = '') {
        // Detect Indian stocks by symbol suffix or currency parameter
        const isIndianStock = symbol.includes('.NS') || symbol.includes('.BO') || 
                            currency === 'INR' || currency === 'Rs';
        
        if (isIndianStock) {
            // Format for Indian Rupees
            return new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(price);
        } else {
            // Format for US Dollars
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(price);
        }
    }

    formatPercent(percent) {
        return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
    }
}

const dataService = new DataService();