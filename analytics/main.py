from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time
import os
import re
from datetime import datetime
from collections import defaultdict
from services.stock_data import StockDataService
from services.news_service import NewsService
from services.portfolio_service import PortfolioService
# Temporarily disabled - requires scipy
# from services.technical_analysis import TechnicalAnalysis
# from services.risk_analysis import RiskAnalysis
# from services.portfolio_optimization import PortfolioOptimization

# Security-hardened FastAPI configuration
app = FastAPI(
    title="StockSense Analytics API", 
    version="1.0.0",
    docs_url=None if os.getenv("ENV") == "production" else "/docs",
    redoc_url=None if os.getenv("ENV") == "production" else "/redoc",
    openapi_url=None if os.getenv("ENV") == "production" else "/openapi.json"
)

# Rate Limiting Store with caching
rate_limit_store = defaultdict(list)
response_cache = {}  # Cache for responses
RATE_LIMIT_REQUESTS = 300  # Increased to 300 requests per minute (5 per second)
RATE_LIMIT_WINDOW = 60
CACHE_DURATION = 10  # Cache responses for 10 seconds

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware with response caching"""
    client_ip = request.client.host
    current_time = time.time()
    
    # Check if we have a cached response for this exact request
    cache_key = f"{request.method}:{request.url.path}:{request.url.query}"
    if cache_key in response_cache:
        cached_response, cache_time = response_cache[cache_key]
        if current_time - cache_time < CACHE_DURATION:
            # Return cached response without counting against rate limit
            return JSONResponse(
                status_code=200,
                content=cached_response,
                headers={"X-Cache": "HIT"}
            )
        else:
            # Cache expired, remove it
            del response_cache[cache_key]
    
    # Clean expired rate limit entries
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check limit (more lenient for localhost)
    max_requests = RATE_LIMIT_REQUESTS * 2 if client_ip in ['127.0.0.1', 'localhost'] else RATE_LIMIT_REQUESTS
    if len(rate_limit_store[client_ip]) >= max_requests:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": "Rate limit exceeded. Please wait a moment and try again."}
        )
    
    rate_limit_store[client_ip].append(current_time)
    response = await call_next(request)
    
    # Cache successful GET responses
    if request.method == "GET" and response.status_code == 200:
        # Only cache if response has content
        if hasattr(response, 'body'):
            try:
                import json
                response_body = json.loads(response.body)
                response_cache[cache_key] = (response_body, current_time)
                # Limit cache size to prevent memory issues
                if len(response_cache) > 1000:
                    # Remove oldest entries
                    oldest_keys = sorted(response_cache.keys(), key=lambda k: response_cache[k][1])[:100]
                    for key in oldest_keys:
                        del response_cache[key]
            except:
                pass
    
    return response

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# CORS Configuration
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "*"]
)

# Gzip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Input Validation Helper
def validate_symbol(symbol: str) -> str:
    """Validate and sanitize stock symbol"""
    if not symbol or len(symbol) > 20:  # Increased to 20 for Indian stocks with .NS/.BO suffix
        raise HTTPException(status_code=400, detail="Invalid symbol length")
    # Allow alphanumeric characters, dots, hyphens, carets, and spaces (for company names)
    if not re.match(r'^[A-Za-z0-9.\s^-]+$', symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format")
    return symbol.upper()

def validate_limit(limit: int, max_limit: int = 100) -> int:
    """Validate limit parameter"""
    if limit < 1 or limit > max_limit:
        raise HTTPException(status_code=400, detail=f"Limit must be between 1 and {max_limit}")
    return limit

# technical_analysis = TechnicalAnalysis()
# risk_analysis = RiskAnalysis()
# portfolio_optimization = PortfolioOptimization()
stock_data_service = StockDataService()
news_service = NewsService()
portfolio_service = PortfolioService()

@app.get("/")
async def root():
    return {"message": "StockSense Analytics API", "status": "running", "version": "1.0.0"}

@app.get("/api/analyze/{symbol}")
async def analyze_stock(symbol: str, type: str = "technical"):
    """Perform advanced stock analysis using Python ML"""
    symbol = validate_symbol(symbol)
    # Temporarily disabled - requires scipy installation
    raise HTTPException(status_code=501, detail="Analysis features coming soon - install scipy for full functionality")

@app.post("/api/portfolio/optimize")
async def optimize_portfolio(data: dict):
    """Optimize portfolio using Markowitz Modern Portfolio Theory"""
    # Temporarily disabled - requires scipy installation
    raise HTTPException(status_code=501, detail="Portfolio optimization coming soon - install scipy for full functionality")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "python-analytics"}

@app.get("/api/stock/quote/{symbol}")
async def get_stock_quote(symbol: str):
    """Get real-time stock quote using yfinance"""
    symbol = validate_symbol(symbol)
    try:
        quote = stock_data_service.get_quote(symbol)
        if not quote:
            raise HTTPException(status_code=404, detail="Symbol not found")
        return quote
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_stock_quote: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock quote")

@app.get("/api/stock/historical/{symbol}")
async def get_historical_data(symbol: str, period: str = "1mo", interval: str = "1d"):
    """Get historical stock data"""
    symbol = validate_symbol(symbol)
    
    # Validate period and interval
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail="Invalid period")
    if interval not in valid_intervals:
        raise HTTPException(status_code=400, detail="Invalid interval")
    
    try:
        data = stock_data_service.get_historical_data(symbol, period, interval)
        return data
    except Exception as e:
        print(f"Error in get_historical_data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch historical data")

@app.get("/api/stock/search")
async def search_stocks(query: str, region: str = "all"):
    """
    Search for ANY stock symbols worldwide (case-insensitive)
    
    Parameters:
    - query: Search term in any case (e.g., "apple", "APPLE", "Apple")
    - region: 'all' (default), 'us', 'india', or specific exchange code
    
    Searches by company name or symbol (works with both lowercase and uppercase)
    """
    if not query or len(query) > 50:
        raise HTTPException(status_code=400, detail="Invalid query")
    
    # Sanitize query - remove special characters except spaces and alphanumeric
    # Keep original case for better matching
    query = re.sub(r'[^a-zA-Z0-9\s.-]', '', query).strip()
    
    # Validate region
    if region not in ['all', 'us', 'india'] and len(region) > 10:
        region = 'all'
    
    try:
        results = stock_data_service.search_symbols(query, region)
        return {
            "results": results, 
            "count": len(results),
            "query": query,
            "region": region,
            "case_insensitive": True
        }
    except Exception as e:
        print(f"Error in search_stocks: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/api/stock/nse/quote/{symbol}")
async def get_nse_quote(symbol: str):
    """
    Get real-time quote from NSE using NSEPy library
    Provides NSE-specific data including trades and deliverable volume
    """
    if not symbol or len(symbol) > 20:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    
    try:
        quote = stock_data_service.get_nse_quote(symbol)
        if 'error' in quote:
            raise HTTPException(status_code=404, detail=quote['error'])
        return quote
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_nse_quote: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch NSE quote")

@app.get("/api/stock/nse/historical/{symbol}")
async def get_nse_historical(symbol: str, days: int = 30):
    """
    Get historical data from NSE using NSEPy library
    Includes NSE-specific metrics like trades and deliverable volume
    """
    if not symbol or len(symbol) > 20:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
    
    try:
        data = stock_data_service.get_nse_historical(symbol, days)
        if 'error' in data:
            raise HTTPException(status_code=404, detail=data['error'])
        return data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_nse_historical: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch NSE historical data")

@app.get("/api/stock/indian/comprehensive/{symbol}")
async def get_comprehensive_indian_stock(symbol: str):
    """
    Get comprehensive Indian stock data from multiple sources (yfinance + NSEPy)
    Returns data from both sources for comparison and reliability
    """
    if not symbol or len(symbol) > 20:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    
    try:
        data = stock_data_service.get_comprehensive_indian_data(symbol)
        if 'error' in data and not data.get('sources'):
            raise HTTPException(status_code=404, detail=data['error'])
        return data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_comprehensive_indian_stock: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch comprehensive data")

@app.get("/api/stocks/database/us")
async def get_all_us_stocks_list(refresh: bool = False):
    """
    Get complete list of ALL US stocks (NYSE, NASDAQ, AMEX)
    Cached for 24 hours for fast offline searching
    
    Parameters:
    - refresh: Force refresh the cache (default: false)
    
    Returns: Complete list of US stocks with symbols and names
    """
    try:
        stocks = stock_data_service.get_all_us_stocks(force_refresh=refresh)
        return {
            "market": "US",
            "count": len(stocks),
            "stocks": stocks,
            "cached": not refresh,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching US stocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch US stocks database")

@app.get("/api/stocks/database/nse")
async def get_all_nse_stocks_list(refresh: bool = False):
    """
    Get complete list of ALL NSE stocks (~2000+ stocks)
    Cached for 24 hours for fast offline searching
    
    Parameters:
    - refresh: Force refresh the cache (default: false)
    
    Returns: Complete list of NSE stocks with symbols and names
    """
    try:
        stocks = stock_data_service.get_all_nse_stocks(force_refresh=refresh)
        return {
            "market": "NSE",
            "count": len(stocks),
            "stocks": stocks,
            "cached": not refresh,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching NSE stocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch NSE stocks database")

@app.get("/api/stocks/database/bse")
async def get_all_bse_stocks_list(refresh: bool = False):
    """
    Get complete list of ALL BSE stocks
    Cached for 24 hours for fast offline searching
    
    Parameters:
    - refresh: Force refresh the cache (default: false)
    
    Returns: Complete list of BSE stocks with symbols and names
    """
    try:
        stocks = stock_data_service.get_all_bse_stocks(force_refresh=refresh)
        return {
            "market": "BSE",
            "count": len(stocks),
            "stocks": stocks,
            "cached": not refresh,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching BSE stocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch BSE stocks database")

@app.get("/api/stocks/database/all")
async def get_all_stocks_database(refresh: bool = False):
    """
    Get complete database of ALL stocks from US, NSE, and BSE
    Cached for 24 hours for fast offline searching
    
    Parameters:
    - refresh: Force refresh the cache (default: false)
    
    Returns: Complete database with stocks from all markets
    """
    try:
        stocks = stock_data_service.get_all_stocks_database(force_refresh=refresh)
        
        total = sum(len(market_stocks) for market_stocks in stocks.values())
        
        return {
            "markets": {
                "us": {"count": len(stocks['us']), "stocks": stocks['us']},
                "nse": {"count": len(stocks['nse']), "stocks": stocks['nse']},
                "bse": {"count": len(stocks['bse']), "stocks": stocks['bse']}
            },
            "total_count": total,
            "cached": not refresh,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching complete stocks database: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stocks database")

@app.get("/api/stocks/search/offline")
async def search_stocks_offline(query: str, market: str = "all"):
    """
    Search stocks using cached database - INSTANT, case-insensitive
    
    Parameters:
    - query: Search term in any case (e.g., "apple", "APPLE", "reliance", "RELIANCE")
    - market: 'all', 'us', 'india', 'nse', or 'bse'
    
    Features:
    - Case-insensitive search
    - Works with company name or symbol
    - Instant results (no API calls)
    - Searches both lowercase and uppercase
    """
    if not query or len(query) > 50:
        raise HTTPException(status_code=400, detail="Invalid query")
    
    # Keep original case for better matching, sanitize special characters
    query = re.sub(r'[^a-zA-Z0-9\s.-]', '', query).strip()
    
    try:
        results = stock_data_service.search_offline(query, market)
        return {
            "results": results,
            "count": len(results),
            "query": query,
            "market": market,
            "source": "cached_database",
            "case_insensitive": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error in offline search: {e}")
        raise HTTPException(status_code=500, detail="Offline search failed")

@app.get("/api/stocks/cache/status")
async def get_cache_status():
    """
    Get status of cached stock databases
    Shows cache age, validity, and stock counts
    """
    try:
        status = stock_data_service.get_cache_status()
        return {
            "cache_status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache status")

@app.get("/api/news/general")
async def get_general_news(limit: int = 10, region: str = 'us'):
    """Get general financial news. Region: 'us' for US market, 'in' for Indian market"""
    limit = validate_limit(limit, max_limit=50)
    
    # Validate region
    if region not in ['us', 'in']:
        region = 'us'
    
    try:
        news = news_service.get_general_news(limit, region)
        return {"news": news, "count": len(news), "region": region}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/{symbol}")
async def get_stock_news(symbol: str, limit: int = 10):
    """Get news for a specific stock"""
    symbol = validate_symbol(symbol)
    limit = validate_limit(limit, max_limit=50)
    
    try:
        news = news_service.get_stock_news(symbol, limit)
        return {"symbol": symbol, "news": news, "count": len(news)}
    except Exception as e:
        print(f"Error in get_stock_news: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")

@app.post("/api/portfolio/analyze")
async def analyze_portfolio(data: dict):
    """Analyze portfolio holdings"""
    try:
        holdings = data.get("holdings", [])
        if not holdings:
            raise HTTPException(status_code=400, detail="No holdings provided")
        
        # Validate holdings data
        if not isinstance(holdings, list) or len(holdings) > 100:
            raise HTTPException(status_code=400, detail="Invalid holdings data")
        
        for holding in holdings:
            if not isinstance(holding, dict):
                raise HTTPException(status_code=400, detail="Invalid holding format")
            if "symbol" not in holding or "shares" not in holding:
                raise HTTPException(status_code=400, detail="Missing required fields")
            validate_symbol(holding["symbol"])
            if not isinstance(holding["shares"], (int, float)) or holding["shares"] <= 0:
                raise HTTPException(status_code=400, detail="Invalid shares value")
        
        analysis = portfolio_service.analyze_portfolio(holdings)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/performance")
async def get_portfolio_performance(data: dict):
    """Get portfolio performance over time"""
    try:
        holdings = data.get("holdings", [])
        period = data.get("period", "1mo")
        
        if not holdings:
            raise HTTPException(status_code=400, detail="No holdings provided")
        
        performance = portfolio_service.get_portfolio_performance(holdings, period)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/diversification")
async def get_diversification(data: dict):
    """Get portfolio diversification score"""
    try:
        holdings = data.get("holdings", [])
        if not holdings:
            raise HTTPException(status_code=400, detail="No holdings provided")
        
        score = portfolio_service.get_diversification_score(holdings)
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI/ML Prediction Endpoints
@app.get("/api/ai/predict/lstm")
async def lstm_prediction(
    symbol: str,
    period: str = "2y",
    simulations: int = 5,
    future_days: int = 30
):
    """
    LSTM-based stock price prediction
    
    Args:
        symbol: Stock symbol or company name (case-insensitive)
        period: Historical data period (1y, 2y, 5y, max)
        simulations: Number of simulations to run
        future_days: Number of future days to predict
    """
    try:
        from services.lstm_prediction import run_lstm_prediction
        from services.company_search import get_symbol_from_query
        
        # Convert company name to symbol if needed
        resolved_symbol = get_symbol_from_query(symbol)
        
        # Validate inputs
        if simulations < 1 or simulations > 10:
            raise HTTPException(status_code=400, detail="Simulations must be between 1 and 10")
        if future_days < 1 or future_days > 90:
            raise HTTPException(status_code=400, detail="Future days must be between 1 and 90")
        
        result = run_lstm_prediction(
            symbol=resolved_symbol,
            period=period,
            num_simulations=simulations,
            future_days=future_days
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Prediction failed'))
        
        # Add query info to response
        result['original_query'] = symbol
        result['resolved_symbol'] = resolved_symbol
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LSTM prediction error: {str(e)}")

@app.get("/api/ai/trading-agent")
async def trading_agent(
    symbol: str,
    period: str = "1y",
    initial_fund: float = 10000,
    skip_days: int = 5,
    strategy: str = "ma"
):
    """
    Run trading agent simulation
    
    Args:
        symbol: Stock symbol
        period: Historical data period
        initial_fund: Starting capital
        skip_days: Days to skip between trades
        strategy: Strategy to use (ma, momentum, rsi)
    """
    try:
        from services.trading_agent import run_trading_agent
        
        # Validate inputs
        if initial_fund < 100 or initial_fund > 1000000:
            raise HTTPException(status_code=400, detail="Initial fund must be between $100 and $1,000,000")
        if skip_days < 1 or skip_days > 30:
            raise HTTPException(status_code=400, detail="Skip days must be between 1 and 30")
        if strategy not in ['ma', 'momentum', 'rsi']:
            raise HTTPException(status_code=400, detail="Strategy must be 'ma', 'momentum', or 'rsi'")
        
        result = run_trading_agent(
            symbol=symbol,
            period=period,
            initial_fund=initial_fund,
            skip_days=skip_days,
            strategy=strategy
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Trading simulation failed'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trading agent error: {str(e)}")

@app.get("/api/ai/download-indian-stocks")
async def download_indian_stocks(period: str = "1y"):
    """
    Download all Indian stocks data (200+ stocks)
    This is a bulk operation that may take several minutes
    
    Args:
        period: Historical data period (1y, 2y, 5y)
    """
    try:
        from services.stock_data_fetcher import download_all_indian_stocks
        
        result = download_all_indian_stocks(period=period)
        
        return {
            'success': True,
            'stocks_downloaded': len(result),
            'stocks': list(result.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading Indian stocks: {str(e)}")

@app.get("/api/ai/download-us-stocks")
async def download_us_stocks(period: str = "1y"):
    """
    Download all US stocks data (300+ stocks)
    This is a bulk operation that may take several minutes
    
    Args:
        period: Historical data period (1y, 2y, 5y)
    """
    try:
        from services.stock_data_fetcher import download_all_us_stocks
        
        result = download_all_us_stocks(period=period)
        
        return {
            'success': True,
            'stocks_downloaded': len(result),
            'stocks': list(result.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading US stocks: {str(e)}")

@app.post("/api/ai/train-models")
async def train_models(period: str = "1y", epochs: int = 10):
    """
    Train LSTM models on all stocks (500+ stocks)
    This is a LONG operation (30-60 minutes)
    Downloads data and trains models for all Indian and US stocks
    
    Args:
        period: Historical data period (1y, 2y, 5y)
        epochs: Training epochs per stock (default: 10)
    """
    try:
        from services.model_trainer import run_full_training_pipeline
        
        # Validate inputs
        if period not in ['1y', '2y', '5y']:
            raise HTTPException(status_code=400, detail="Period must be '1y', '2y', or '5y'")
        if epochs < 5 or epochs > 50:
            raise HTTPException(status_code=400, detail="Epochs must be between 5 and 50")
        
        result = run_full_training_pipeline(period=period, epochs=epochs)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Training failed'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training error: {str(e)}")

@app.get("/api/ai/training-status")
async def training_status():
    """
    Get status of all trained models
    Shows how many models are available and training statistics
    """
    try:
        from services.model_trainer import ModelTrainer
        
        trainer = ModelTrainer()
        status = trainer.get_training_status()
        
        if status is None:
            return {
                'success': True,
                'models_available': 0,
                'message': 'No trained models found. Run /api/ai/train-models to train.'
            }
        
        return {
            'success': True,
            **status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")

@app.get("/api/search/company")
async def search_company(query: str):
    """
    Search for companies by name or symbol
    
    Args:
        query: Company name or stock symbol (case-insensitive)
        
    Returns:
        Search results with symbol, company name, and match confidence
    """
    try:
        from services.company_search import search_company
        
        if not query or len(query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = search_company(query)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/api/search/list-companies")
async def list_companies(limit: int = 50):
    """
    List available companies
    
    Args:
        limit: Maximum number of companies to return (default: 50)
        
    Returns:
        List of companies with names and symbols
    """
    try:
        from services.company_search import list_available_companies
        
        companies = list_available_companies(limit)
        return {
            'success': True,
            'count': len(companies),
            'companies': companies
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List companies error: {str(e)}")


@app.get("/api/ai/predict/lstm-pretrained")
async def lstm_prediction_pretrained(
    symbol: str,
    period: str = "2y",
    future_days: int = 30,
    include_visualization: bool = False
):
    """
    FAST LSTM prediction using pre-trained model
    Falls back to training if no pre-trained model exists
    
    Args:
        symbol: Stock symbol or company name (case-insensitive)
        period: Historical data period (only used if no pre-trained model)
        future_days: Number of days to predict
        include_visualization: Generate chart visualization (base64 encoded)
    """
    try:
        from services.lstm_prediction import run_lstm_prediction_pretrained
        from services.company_search import get_symbol_from_query
        
        # Convert company name to symbol if needed
        resolved_symbol = get_symbol_from_query(symbol)
        
        # Validate inputs
        if future_days < 1 or future_days > 90:
            raise HTTPException(status_code=400, detail="Future days must be between 1 and 90")
        
        result = run_lstm_prediction_pretrained(
            symbol=resolved_symbol,
            period=period,
            future_days=future_days
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Prediction failed'))
        
        # Add original query to response
        result['original_query'] = symbol
        result['resolved_symbol'] = resolved_symbol
        
        # Generate visualization if requested
        if include_visualization:
            try:
                from services.prediction_visualizer import generate_prediction_visualization
                chart_base64 = generate_prediction_visualization(result, output_format='base64')
                result['visualization'] = chart_base64
            except Exception as viz_error:
                print(f"Visualization error: {viz_error}")
                result['visualization_error'] = str(viz_error)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LSTM prediction error: {str(e)}")


@app.get("/api/ai/visualization/prediction-chart")
async def get_prediction_chart(
    symbol: str,
    future_days: int = 30
):
    """
    Generate and return a prediction chart visualization
    
    Args:
        symbol: Stock symbol or company name
        future_days: Number of days to predict
        
    Returns:
        Base64 encoded PNG image
    """
    try:
        from services.lstm_prediction import run_lstm_prediction_pretrained
        from services.company_search import get_symbol_from_query
        from services.prediction_visualizer import generate_prediction_visualization
        
        # Convert company name to symbol
        resolved_symbol = get_symbol_from_query(symbol)
        
        # Get prediction data
        result = run_lstm_prediction_pretrained(
            symbol=resolved_symbol,
            period="6mo",
            future_days=future_days
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Prediction failed'))
        
        # Generate visualization
        chart_base64 = generate_prediction_visualization(result, output_format='base64')
        
        return {
            'success': True,
            'symbol': resolved_symbol,
            'chart': chart_base64,
            'format': 'base64_png'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation error: {str(e)}")


@app.get("/api/ai/visualization/comprehensive-analysis")
async def get_comprehensive_analysis(
    symbol: str,
    future_days: int = 30
):
    """
    Generate comprehensive analysis with multiple charts
    
    Args:
        symbol: Stock symbol or company name
        future_days: Number of days to predict
        
    Returns:
        Base64 encoded PNG image with multiple analysis charts
    """
    try:
        from services.lstm_prediction import run_lstm_prediction_pretrained
        from services.company_search import get_symbol_from_query
        from services.prediction_visualizer import generate_comprehensive_analysis
        
        # Convert company name to symbol
        resolved_symbol = get_symbol_from_query(symbol)
        
        # Get prediction data
        result = run_lstm_prediction_pretrained(
            symbol=resolved_symbol,
            period="6mo",
            future_days=future_days
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Prediction failed'))
        
        # Generate comprehensive analysis
        chart_base64 = generate_comprehensive_analysis(result, output_format='base64')
        
        return {
            'success': True,
            'symbol': resolved_symbol,
            'chart': chart_base64,
            'format': 'base64_png',
            'includes': ['price_prediction', 'distribution', 'returns', 'volatility', 'metrics']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis generation error: {str(e)}")


@app.get("/api/ai/visualization/enhanced-dashboard")
async def get_enhanced_dashboard(
    symbol: str,
    future_days: int = 30
):
    """
    Generate enhanced AI dashboard with 9 advanced visualizations
    
    Args:
        symbol: Stock symbol or company name
        future_days: Number of days to predict
        
    Returns:
        Base64 encoded PNG image with advanced dashboard
    """
    try:
        from services.lstm_prediction import run_lstm_prediction_pretrained
        from services.company_search import get_symbol_from_query
        from services.enhanced_visualizer import generate_enhanced_dashboard
        
        # Convert company name to symbol
        resolved_symbol = get_symbol_from_query(symbol)
        
        # Get prediction data
        result = run_lstm_prediction_pretrained(
            symbol=resolved_symbol,
            period="6mo",
            future_days=future_days
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Prediction failed'))
        
        # Generate enhanced dashboard
        chart_base64 = generate_enhanced_dashboard(result, output_format='base64')
        
        return {
            'success': True,
            'symbol': resolved_symbol,
            'chart': chart_base64,
            'format': 'base64_png',
            'dashboard_type': 'enhanced',
            'includes': [
                'main_prediction',
                'price_momentum',
                'volatility_gauge',
                'technical_summary',
                'confidence_meter',
                'returns_distribution',
                'accuracy_metrics',
                'risk_gauge'
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard generation error: {str(e)}")


# Company Search Endpoints

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)