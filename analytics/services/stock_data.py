import yfinance as yf
from datetime import datetime, timedelta
from .indian_stock_service import IndianStockService
from .universal_stock_search import UniversalStockSearch
from .stock_list_cache import StockListCache

class StockDataService:
    def __init__(self):
        # Initialize Indian stock service for enhanced Indian stock search
        self.indian_service = IndianStockService(finnhub_api_key="d43h6l1r01qvk0jbscngd43h6l1r01qvk0jbsco0")
        # Initialize universal search for ANY stock worldwide
        self.universal_search = UniversalStockSearch(finnhub_api_key="d43h6l1r01qvk0jbscngd43h6l1r01qvk0jbsco0")
        # Initialize stock list cache for offline searching
        self.stock_cache = StockListCache()
    
    def get_quote(self, symbol: str) -> dict:
        """Get real-time stock quote using yfinance, with enhanced support for Indian stocks"""
        try:
            # Check if it's an Indian stock (has .NS or .BO suffix)
            is_indian = '.NS' in symbol.upper() or '.BO' in symbol.upper()
            
            # If it has Indian suffix, try Indian service first
            if is_indian:
                try:
                    indian_data = self.indian_service.get_yfinance_realtime_data(symbol)
                    if 'error' not in indian_data:
                        return indian_data
                except Exception as e:
                    print(f"Indian service failed for {symbol}, falling back to standard: {e}")
            
            # Standard yfinance logic for US stocks and fallback
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="2d")
            
            if hist.empty or len(hist) < 1:
                raise ValueError(f"No data available for {symbol}")
            
            current_price = hist['Close'].iloc[-1]
            prev_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
            
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
            
            # Determine currency based on symbol or info
            currency = 'USD'
            if '.NS' in symbol or '.BO' in symbol:
                currency = 'INR'
            else:
                currency = info.get('currency', 'USD')
            
            return {
                "symbol": symbol.upper(),
                "name": info.get('longName', symbol),
                "price": round(float(current_price), 2),
                "open": round(float(hist['Open'].iloc[-1]), 2) if 'Open' in hist else 0,
                "high": round(float(hist['High'].iloc[-1]), 2) if 'High' in hist else 0,
                "low": round(float(hist['Low'].iloc[-1]), 2) if 'Low' in hist else 0,
                "volume": int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0,
                "change": round(float(change), 2),
                "changePercent": round(float(change_percent), 2),
                "previousClose": round(float(prev_close), 2),
                "marketCap": info.get('marketCap', 0),
                "currency": currency,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error fetching quote for {symbol}: {e}")
            raise
    
    def get_historical_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> dict:
        """Get historical stock data with enhanced support for Indian stocks"""
        try:
            # Check if it's an Indian stock (has .NS or .BO suffix)
            is_indian = '.NS' in symbol.upper() or '.BO' in symbol.upper()
            
            # Only try Indian service if it explicitly has Indian suffix
            if is_indian:
                try:
                    # Try using the Indian service which supports NSE/BSE stocks
                    indian_data = self.indian_service.get_historical_data(symbol, period, interval)
                    if 'error' not in indian_data:
                        return indian_data
                except Exception as e:
                    print(f"Indian service failed for {symbol}, falling back to standard: {e}")
            
            # Standard yfinance logic
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                raise ValueError(f"No historical data for {symbol}")
            
            dates = [date.strftime('%Y-%m-%d') for date in hist.index]
            
            return {
                "symbol": symbol.upper(),
                "dates": dates,
                "open": [round(float(x), 2) for x in hist['Open'].tolist()],
                "high": [round(float(x), 2) for x in hist['High'].tolist()],
                "low": [round(float(x), 2) for x in hist['Low'].tolist()],
                "close": [round(float(x), 2) for x in hist['Close'].tolist()],
                "volume": [int(x) for x in hist['Volume'].tolist()],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            raise
    
    def search_symbols(self, query: str, region: str = "all") -> list:
        """
        Search for ANY stock symbols worldwide using Finnhub API
        
        Args:
            query: Search term (company name, symbol, etc.)
            region: 'all', 'us', 'india', or specific exchange code
        
        Returns:
            List of matching stocks from any exchange
        """
        results = []
        seen_symbols = set()
        
        # Step 1: Check local Indian company mapping first (fastest)
        try:
            if region in ['all', 'india']:
                indian_local = self.indian_service.search_companies(query)
                for item in indian_local:
                    symbol_key = item.get('symbol', '') + item.get('nse_symbol', '')
                    if symbol_key not in seen_symbols:
                        results.append(item)
                        seen_symbols.add(symbol_key)
        except Exception as e:
            print(f"Local Indian search error: {e}")
        
        # Step 2: Use Finnhub to search stocks (filtered to US and Indian markets by default)
        try:
            if region == 'all':
                # Search all exchanges but filter to US and Indian markets only
                universal_results = self.universal_search.search_all_stocks(query, limit=50, filter_markets=True)
            elif region == 'us':
                # Search only US stocks
                universal_results = self.universal_search.search_us_stocks(query, limit=50)
            elif region == 'india':
                # Search only Indian stocks
                universal_results = self.universal_search.search_indian_stocks(query, limit=50)
            else:
                # Search specific exchange
                universal_results = self.universal_search.search_by_exchange(query, region, limit=50)
            
            # Add results, avoiding duplicates
            for item in universal_results:
                symbol = item.get('symbol', '')
                if symbol and symbol not in seen_symbols:
                    results.append(item)
                    seen_symbols.add(symbol)
        except Exception as e:
            print(f"Universal search error: {e}")
        
        # Return top 30 results
        return results[:30]
    
    def get_nse_quote(self, symbol):
        """
        Get real-time quote from NSE using NSEPy
        """
        try:
            return self.indian_service.get_nsepy_quote(symbol)
        except Exception as e:
            print(f"Error getting NSE quote: {e}")
            raise
    
    def get_nse_historical(self, symbol, days=30):
        """
        Get historical data from NSE using NSEPy
        """
        try:
            from datetime import date, timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            return self.indian_service.get_nsepy_historical_data(symbol, start_date, end_date)
        except Exception as e:
            print(f"Error getting NSE historical data: {e}")
            raise
    
    def get_comprehensive_indian_data(self, symbol):
        """
        Get comprehensive Indian stock data from multiple sources
        """
        try:
            return self.indian_service.get_comprehensive_data(symbol, data_type="quote")
        except Exception as e:
            print(f"Error getting comprehensive data: {e}")
            raise
    
    def get_all_us_stocks(self, force_refresh=False):
        """
        Get complete list of ALL US stocks (cached)
        """
        return self.stock_cache.get_us_stocks(force_refresh)
    
    def get_all_nse_stocks(self, force_refresh=False):
        """
        Get complete list of ALL NSE stocks (cached)
        """
        return self.stock_cache.get_nse_stocks(force_refresh)
    
    def get_all_bse_stocks(self, force_refresh=False):
        """
        Get complete list of ALL BSE stocks (cached)
        """
        return self.stock_cache.get_bse_stocks(force_refresh)
    
    def get_all_stocks_database(self, force_refresh=False):
        """
        Get complete database of ALL stocks from US, NSE, and BSE
        """
        return self.stock_cache.get_all_stocks(force_refresh)
    
    def search_offline(self, query, market='all'):
        """
        Search stocks using cached database (no API calls, instant results)
        """
        return self.stock_cache.search_cached_stocks(query, market)
    
    def get_cache_status(self):
        """
        Get status of cached stock lists
        """
        return self.stock_cache.get_cache_info()
