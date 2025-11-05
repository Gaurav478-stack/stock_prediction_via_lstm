import yfinance as yf
from datetime import datetime, timedelta, date
import warnings
import requests
from nsepy import get_history
from nsepy.history import get_price_list
import pandas as pd
warnings.filterwarnings('ignore')

class IndianStockService:
    def __init__(self, alpha_vantage_api_key=None, finnhub_api_key=None):
        """
        Initialize the Indian Stock Service with company name to symbol mapping and NSEPy
        """
        self.alpha_vantage_key = alpha_vantage_api_key
        self.finnhub_key = finnhub_api_key
        
        # Comprehensive mapping of company names to symbols
        self.company_to_symbol = {
            # Large Cap
            'reliance': 'RELIANCE', 'reliance industries': 'RELIANCE', 'ril': 'RELIANCE',
            'tata consultancy services': 'TCS', 'tcs': 'TCS',
            'infosys': 'INFY',
            'hdfc bank': 'HDFCBANK', 'hdfc': 'HDFCBANK',
            'icici bank': 'ICICIBANK', 'icici': 'ICICIBANK',
            'state bank of india': 'SBIN', 'sbi': 'SBIN',
            'hindustan unilever': 'HINDUNILVR', 'hul': 'HINDUNILVR',
            'itc': 'ITC',
            'bharti airtel': 'BHARTIARTL', 'airtel': 'BHARTIARTL',
            'kotak mahindra bank': 'KOTAKBANK', 'kotak bank': 'KOTAKBANK',
            'larsen & toubro': 'LT', 'l&t': 'LT',
            'axis bank': 'AXISBANK',
            'bajaj finance': 'BAJFINANCE',
            
            # Tech Companies
            'wipro': 'WIPRO',
            'tech mahindra': 'TECHM',
            'hcl technologies': 'HCLTECH', 'hcl': 'HCLTECH',
            'ltimindtree': 'LTIM',
            'persistent systems': 'PERSISTENT',
            'mphasis': 'MPHASIS',
            
            # Auto
            'tata motors': 'TATAMOTORS',
            'maruti suzuki': 'MARUTI', 'maruti': 'MARUTI',
            'mahindra & mahindra': 'M&M', 'mahindra': 'M&M',
            'bajaj auto': 'BAJAJ-AUTO',
            'hero motocorp': 'HEROMOTOCO',
            'eicher motors': 'EICHERMOT',
            'tata steel': 'TATASTEEL',
            
            # Pharma
            'sun pharmaceutical': 'SUNPHARMA', 'sun pharma': 'SUNPHARMA',
            'dr reddys laboratories': 'DRREDDY', 'dr reddys': 'DRREDDY',
            'cipla': 'CIPLA',
            'divis laboratories': 'DIVISLAB',
            'apollo hospitals': 'APOLLOHOSP',
            
            # FMCG
            'nestle india': 'NESTLEIND', 'nestle': 'NESTLEIND',
            'britannia industries': 'BRITANNIA', 'britannia': 'BRITANNIA',
            'godrej consumer': 'GODREJCP',
            'dabur': 'DABUR',
            'marico': 'MARICO',
            'tata consumer': 'TATACONSUM',
            
            # Energy & Power
            'ongc': 'ONGC',
            'ntpc': 'NTPC',
            'power grid': 'POWERGRID',
            'bpcl': 'BPCL',
            'coal india': 'COALINDIA',
            'adani green': 'ADANIGREEN',
            
            # Cement
            'asian paints': 'ASIANPAINT',
            'titan company': 'TITAN', 'titan': 'TITAN',
            'ultratech cement': 'ULTRACEMCO', 'ultratech': 'ULTRACEMCO',
            'shree cement': 'SHREECEM',
            'grasim industries': 'GRASIM',
            
            # Adani Group
            'adani enterprises': 'ADANIENT',
            'adani ports': 'ADANIPORTS',
            
            # Insurance & Finance
            'hdfc life': 'HDFCLIFE',
            'sbi life': 'SBILIFE',
            'bajaj finserv': 'BAJAJFINSV',
            'indusind bank': 'INDUSINDBK',
            
            # Metals & Mining
            'jsw steel': 'JSWSTEEL',
            'hindalco': 'HINDALCO',
            'vedanta': 'VEDL',
            
            # New Age Tech
            'zomato': 'ZOMATO',
            'paytm': 'PAYTM',
            'nykaa': 'NYKAA',
            'policybazaar': 'POLICYBZR',
            'irctc': 'IRCTC',
            
            # Defense & PSU
            'hal': 'HAL', 'hindustan aeronautics': 'HAL',
            'bel': 'BEL', 'bharat electronics': 'BEL',
            
            # Others
            'pidilite': 'PIDILITIND'
        }
    
    def find_symbol(self, company_name):
        """
        Convert company name to stock symbol
        """
        company_name_lower = company_name.lower().strip()
        
        # Direct mapping lookup
        if company_name_lower in self.company_to_symbol:
            return self.company_to_symbol[company_name_lower]
        
        # Fuzzy matching for partial names
        for name, symbol in self.company_to_symbol.items():
            if company_name_lower in name or name in company_name_lower:
                return self.company_to_symbol[name]
        
        # If not found, try to search using the first word
        words = company_name_lower.split()
        if words:
            first_word = words[0]
            for name, symbol in self.company_to_symbol.items():
                if first_word in name:
                    return self.company_to_symbol[name]
        
        return None
    
    def get_company_info(self, company_name):
        """
        Get basic company information and symbol
        """
        symbol = self.find_symbol(company_name)
        if not symbol:
            return {"error": f"Company '{company_name}' not found in database"}
        
        return {
            'company_name': company_name.title(),
            'symbol': symbol,
            'nse_symbol': f"{symbol}.NS",
            'bse_symbol': f"{symbol}.BO"
        }
    
    def get_yfinance_realtime_data(self, company_name_or_symbol):
        """
        Get real-time data using yfinance with company name or symbol
        """
        # Try to get company info first (handles both names and symbols)
        company_info = self.get_company_info(company_name_or_symbol)
        
        # If not found in mapping, assume it's already a valid symbol
        if 'error' in company_info:
            symbol_with_suffix = company_name_or_symbol if '.NS' in company_name_or_symbol or '.BO' in company_name_or_symbol else f"{company_name_or_symbol}.NS"
            company_info = {
                'symbol': company_name_or_symbol,
                'nse_symbol': symbol_with_suffix
            }
        
        try:
            symbol_with_suffix = company_info['nse_symbol']
            stock = yf.Ticker(symbol_with_suffix)
            info = stock.info
            hist = stock.history(period="2d")
            
            # Get current price from the latest available data
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                volume = hist['Volume'].iloc[-1]
                day_high = hist['High'].iloc[-1]
                day_low = hist['Low'].iloc[-1]
                day_open = hist['Open'].iloc[-1]
            else:
                current_price = info.get('currentPrice', 0)
                volume = info.get('volume', 0)
                day_high = info.get('dayHigh', 0)
                day_low = info.get('dayLow', 0)
                day_open = info.get('open', 0)
            
            previous_close = info.get('previousClose', current_price)
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
            
            return {
                'company_info': company_info,
                'symbol': company_info.get('symbol', company_name_or_symbol),
                'name': info.get('longName', company_info.get('company_name', company_name_or_symbol)),
                'price': round(float(current_price), 2),
                'current_price': round(float(current_price), 2),
                'open': round(float(day_open), 2),
                'high': round(float(day_high), 2),
                'low': round(float(day_low), 2),
                'day_high': round(float(day_high), 2),
                'day_low': round(float(day_low), 2),
                'volume': int(volume),
                'change': round(float(change), 2),
                'changePercent': round(float(change_percent), 2),
                'previous_close': round(float(previous_close), 2),
                'previousClose': round(float(previous_close), 2),
                'currency': info.get('currency', 'INR'),
                'market_cap': info.get('marketCap', 0),
                'marketCap': info.get('marketCap', 0),
                'data_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': datetime.now().isoformat(),
                'source': 'Yahoo Finance'
            }
        except Exception as e:
            print(f"YFinance error for {company_name_or_symbol}: {e}")
            return {"error": f"YFinance error: {str(e)}"}
    
    def get_historical_data(self, company_name_or_symbol, period: str = "1mo", interval: str = "1d"):
        """
        Get historical data using yfinance
        """
        # Try to get company info first
        company_info = self.get_company_info(company_name_or_symbol)
        
        # If not found in mapping, assume it's already a valid symbol
        if 'error' in company_info:
            symbol_with_suffix = company_name_or_symbol if '.NS' in company_name_or_symbol or '.BO' in company_name_or_symbol else f"{company_name_or_symbol}.NS"
            company_info = {
                'symbol': company_name_or_symbol,
                'nse_symbol': symbol_with_suffix
            }
        
        try:
            symbol_with_suffix = company_info['nse_symbol']
            ticker = yf.Ticker(symbol_with_suffix)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                raise ValueError(f"No historical data for {symbol_with_suffix}")
            
            dates = [date.strftime('%Y-%m-%d') for date in hist.index]
            
            return {
                "symbol": company_info.get('symbol', company_name_or_symbol),
                "dates": dates,
                "open": [round(float(x), 2) for x in hist['Open'].tolist()],
                "high": [round(float(x), 2) for x in hist['High'].tolist()],
                "low": [round(float(x), 2) for x in hist['Low'].tolist()],
                "close": [round(float(x), 2) for x in hist['Close'].tolist()],
                "volume": [int(x) for x in hist['Volume'].tolist()],
                "timestamp": datetime.now().isoformat(),
                "source": "Yahoo Finance"
            }
        except Exception as e:
            print(f"Error fetching historical data for {company_name_or_symbol}: {e}")
            raise
    
    def search_companies(self, search_term):
        """
        Search for companies by name - case-insensitive, works with lowercase/uppercase
        """
        # Normalize search term to lowercase for case-insensitive matching
        search_lower = search_term.lower().strip()
        matches = []
        seen_symbols = set()
        
        # First pass: exact and prefix matches (higher priority)
        for company_name, symbol in self.company_to_symbol.items():
            if symbol in seen_symbols:
                continue
            
            company_lower = company_name.lower()
            symbol_lower = symbol.lower()
            
            # Exact match or starts with query
            if (company_lower == search_lower or 
                company_lower.startswith(search_lower) or
                symbol_lower == search_lower or
                symbol_lower.startswith(search_lower)):
                matches.append({
                    'company_name': company_name.title(),
                    'symbol': symbol,
                    'nse_symbol': f"{symbol}.NS",
                    'market': 'India (NSE)',
                    'priority': 1
                })
                seen_symbols.add(symbol)
        
        # Second pass: partial matches (lower priority)
        for company_name, symbol in self.company_to_symbol.items():
            if symbol in seen_symbols:
                continue
            
            company_lower = company_name.lower()
            symbol_lower = symbol.lower()
            
            # Contains query
            if search_lower in company_lower or search_lower in symbol_lower:
                matches.append({
                    'company_name': company_name.title(),
                    'symbol': symbol,
                    'nse_symbol': f"{symbol}.NS",
                    'market': 'India (NSE)',
                    'priority': 2
                })
                seen_symbols.add(symbol)
        
        # Sort by priority and return top matches
        matches.sort(key=lambda x: (x['priority'], x['company_name']))
        
        # Remove priority field before returning
        for match in matches:
            match.pop('priority', None)
        
        return matches[:20]
    
    def search_nse_stocks_online(self, search_term):
        """
        Search NSE stocks using yfinance online search
        """
        try:
            # Search for Indian stocks with .NS suffix
            search_results = []
            
            # Try common NSE stock patterns
            possible_symbols = [
                f"{search_term.upper()}.NS",
                f"{search_term.upper()}.BO"
            ]
            
            for symbol in possible_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    if info and info.get('symbol'):
                        search_results.append({
                            'symbol': info.get('symbol', symbol).replace('.NS', '').replace('.BO', ''),
                            'name': info.get('longName', info.get('shortName', symbol)),
                            'nse_symbol': symbol,
                            'market': 'India (NSE)' if '.NS' in symbol else 'India (BSE)',
                            'currency': info.get('currency', 'INR')
                        })
                except:
                    continue
            
            return search_results
        except Exception as e:
            print(f"Error searching NSE stocks online: {e}")
            return []
    
    def get_nsepy_historical_data(self, symbol, start_date=None, end_date=None):
        """
        Get historical data from NSE using NSEPy library
        
        Args:
            symbol: Stock symbol without .NS suffix (e.g., 'RELIANCE', 'TCS')
            start_date: Start date (datetime object or None for last 30 days)
            end_date: End date (datetime object or None for today)
        """
        try:
            # Remove .NS or .BO suffix if present
            clean_symbol = symbol.replace('.NS', '').replace('.BO', '').upper()
            
            # Set default dates if not provided
            if end_date is None:
                end_date = date.today()
            if start_date is None:
                start_date = end_date - timedelta(days=30)
            
            # Fetch data from NSE
            df = get_history(
                symbol=clean_symbol,
                start=start_date,
                end=end_date
            )
            
            if df.empty:
                return {"error": f"No data available for {clean_symbol} from NSE"}
            
            # Convert to JSON format
            dates = [d.strftime('%Y-%m-%d') for d in df.index]
            
            return {
                "symbol": clean_symbol,
                "source": "NSE (NSEPy)",
                "dates": dates,
                "open": [round(float(x), 2) for x in df['Open'].tolist()],
                "high": [round(float(x), 2) for x in df['High'].tolist()],
                "low": [round(float(x), 2) for x in df['Low'].tolist()],
                "close": [round(float(x), 2) for x in df['Close'].tolist()],
                "volume": [int(x) for x in df['Volume'].tolist()],
                "trades": [int(x) for x in df['Trades'].tolist()] if 'Trades' in df else [],
                "deliverable": [int(x) for x in df['Deliverable Volume'].tolist()] if 'Deliverable Volume' in df else [],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"NSEPy error for {symbol}: {e}")
            return {"error": f"NSEPy error: {str(e)}"}
    
    def get_nsepy_quote(self, symbol):
        """
        Get real-time quote from NSE using NSEPy
        """
        try:
            # Remove .NS or .BO suffix if present
            clean_symbol = symbol.replace('.NS', '').replace('.BO', '').upper()
            
            # Get last 2 days data to get current price
            end_date = date.today()
            start_date = end_date - timedelta(days=5)  # Get last 5 days to ensure we have data
            
            df = get_history(
                symbol=clean_symbol,
                start=start_date,
                end=end_date
            )
            
            if df.empty:
                return {"error": f"No data available for {clean_symbol}"}
            
            # Get latest data
            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest
            
            current_price = float(latest['Close'])
            previous_close = float(previous['Close'])
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
            
            return {
                "symbol": clean_symbol,
                "name": clean_symbol,
                "price": round(current_price, 2),
                "open": round(float(latest['Open']), 2),
                "high": round(float(latest['High']), 2),
                "low": round(float(latest['Low']), 2),
                "close": round(current_price, 2),
                "volume": int(latest['Volume']),
                "change": round(change, 2),
                "changePercent": round(change_percent, 2),
                "previousClose": round(previous_close, 2),
                "trades": int(latest['Trades']) if 'Trades' in latest else 0,
                "deliverable": int(latest['Deliverable Volume']) if 'Deliverable Volume' in latest else 0,
                "timestamp": datetime.now().isoformat(),
                "source": "NSE (NSEPy)",
                "currency": "INR"
            }
        except Exception as e:
            print(f"NSEPy quote error for {symbol}: {e}")
            return {"error": f"NSEPy error: {str(e)}"}
    
    def get_comprehensive_data(self, company_name_or_symbol, data_type="quote"):
        """
        Get comprehensive data using multiple sources (yfinance + NSEPy)
        Combines data from both sources for more reliability
        """
        result = {
            "query": company_name_or_symbol,
            "sources": {}
        }
        
        # Try yfinance first
        try:
            if data_type == "quote":
                yf_data = self.get_yfinance_realtime_data(company_name_or_symbol)
                if 'error' not in yf_data:
                    result['sources']['yfinance'] = yf_data
                    result['primary_source'] = 'yfinance'
        except Exception as e:
            print(f"YFinance failed: {e}")
        
        # Try NSEPy
        try:
            # Get symbol from mapping if company name provided
            symbol = self.find_symbol(company_name_or_symbol)
            if not symbol:
                symbol = company_name_or_symbol
            
            if data_type == "quote":
                nse_data = self.get_nsepy_quote(symbol)
                if 'error' not in nse_data:
                    result['sources']['nsepy'] = nse_data
                    if 'primary_source' not in result:
                        result['primary_source'] = 'nsepy'
        except Exception as e:
            print(f"NSEPy failed: {e}")
        
        # If we have data from at least one source, consider it successful
        if result['sources']:
            # Use yfinance as primary if available, fallback to nsepy
            primary = result.get('primary_source', 'yfinance')
            result['data'] = result['sources'].get(primary, list(result['sources'].values())[0])
        else:
            result['error'] = "Failed to fetch data from all sources"
        
        return result
