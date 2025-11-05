// Automatically detect environment
const isProduction = window.location.hostname.includes('github.io') || 
                     window.location.hostname.includes('gaurav478-stack') ||
                     window.location.hostname.includes('onrender.com');

const CONFIG = {
    ALPHA_VANTAGE: {
        BASE_URL: 'https://www.alphavantage.co/query',
        API_KEY: 'RHM3BPM80BKAPFL3',
        RATE_LIMIT_DELAY: 15000, // 15 seconds between calls (safe for 5 calls/min limit)
        ENABLED: false // Disabled in favor of yfinance
    },
    BACKEND: {
        // 🔥 TODO: Replace these URLs with your actual Render URLs after deployment!
        BASE_URL: isProduction 
            ? 'https://stocksense-backend.onrender.com/api'  // REPLACE WITH YOUR BACKEND URL
            : 'http://localhost:3000/api',
        ANALYTICS_URL: isProduction 
            ? 'https://stocksense-analytics.onrender.com/api'  // REPLACE WITH YOUR ANALYTICS URL
            : 'http://localhost:8000/api'
    },
    APP: {
        DEFAULT_WATCHLIST: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'], // Back to 5 stocks - no limits with yfinance!
        CACHE_DURATION: 30 * 1000, // 30 seconds - matches with backend cache
        REFRESH_INTERVAL: 60000
    },
    FEATURES: {
        ENABLE_AI_INSIGHTS: true,
        ENABLE_PYTHON_ANALYTICS: true
    }
};