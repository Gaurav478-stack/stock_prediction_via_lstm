import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class StockListCache:
    def __init__(self, cache_dir="cache"):
        """
        Initialize stock list cache system
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.finnhub_key = "d43h6l1r01qvk0jbscngd43h6l1r01qvk0jbsco0"
        self.cache_duration = 86400  # 24 hours
    
    def _is_cache_valid(self, cache_file):
        """Check if cache file exists and is not expired"""
        if not cache_file.exists():
            return False
        
        # Check file age
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = datetime.now() - file_time
        
        return age.total_seconds() < self.cache_duration
    
    def _load_cache(self, cache_file):
        """Load data from cache file"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
            return None
    
    def _save_cache(self, cache_file, data):
        """Save data to cache file"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving cache: {e}")
            return False
    
    def get_us_stocks(self, force_refresh=False):
        """
        Get complete list of US stocks (NYSE, NASDAQ, AMEX)
        """
        cache_file = self.cache_dir / "us_stocks.json"
        
        # Try to load from cache
        if not force_refresh and self._is_cache_valid(cache_file):
            cached_data = self._load_cache(cache_file)
            if cached_data:
                print(f"Loaded {len(cached_data)} US stocks from cache")
                return cached_data
        
        # Fetch from Finnhub
        print("Fetching US stocks from Finnhub API...")
        all_stocks = []
        
        exchanges = ['US']  # US exchange includes NYSE, NASDAQ, AMEX
        
        for exchange in exchanges:
            try:
                url = f"https://finnhub.io/api/v1/stock/symbol?exchange={exchange}&token={self.finnhub_key}"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    stocks = response.json()
                    
                    for stock in stocks:
                        # Filter out common stock types
                        if stock.get('type') in ['Common Stock', 'EQS', 'ETF']:
                            all_stocks.append({
                                'symbol': stock.get('symbol', ''),
                                'name': stock.get('description', ''),
                                'type': stock.get('type', 'Common Stock'),
                                'currency': stock.get('currency', 'USD'),
                                'market': 'US'
                            })
                    
                    print(f"Fetched {len(stocks)} stocks from {exchange}")
            except Exception as e:
                print(f"Error fetching {exchange} stocks: {e}")
        
        # Save to cache
        if all_stocks:
            self._save_cache(cache_file, all_stocks)
            print(f"Cached {len(all_stocks)} US stocks")
        
        return all_stocks
    
    def get_nse_stocks(self, force_refresh=False):
        """
        Get complete list of NSE stocks
        """
        cache_file = self.cache_dir / "nse_stocks.json"
        
        # Try to load from cache
        if not force_refresh and self._is_cache_valid(cache_file):
            cached_data = self._load_cache(cache_file)
            if cached_data:
                print(f"Loaded {len(cached_data)} NSE stocks from cache")
                return cached_data
        
        # Fetch from multiple sources
        print("Fetching NSE stocks...")
        all_stocks = []
        
        # Method 1: Try NSE India website (stock list CSV)
        try:
            # NSE publishes equity list
            url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.split(',')
                    if len(parts) >= 2:
                        symbol = parts[0].strip().strip('"')
                        name = parts[1].strip().strip('"')
                        
                        if symbol and name:
                            all_stocks.append({
                                'symbol': f"{symbol}.NS",
                                'name': name,
                                'type': 'Common Stock',
                                'currency': 'INR',
                                'market': 'India (NSE)',
                                'nse_symbol': symbol
                            })
                
                print(f"Fetched {len(all_stocks)} stocks from NSE")
        except Exception as e:
            print(f"NSE CSV fetch failed: {e}")
        
        # Method 2: Fallback to Finnhub if NSE direct fetch fails
        if not all_stocks:
            try:
                url = f"https://finnhub.io/api/v1/stock/symbol?exchange=NSE&token={self.finnhub_key}"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    stocks = response.json()
                    
                    for stock in stocks:
                        symbol = stock.get('symbol', '')
                        all_stocks.append({
                            'symbol': symbol,
                            'name': stock.get('description', ''),
                            'type': stock.get('type', 'Common Stock'),
                            'currency': 'INR',
                            'market': 'India (NSE)',
                            'nse_symbol': symbol.replace('.NS', '')
                        })
                    
                    print(f"Fetched {len(all_stocks)} stocks from Finnhub NSE")
            except Exception as e:
                print(f"Finnhub NSE fetch failed: {e}")
        
        # Save to cache
        if all_stocks:
            self._save_cache(cache_file, all_stocks)
            print(f"Cached {len(all_stocks)} NSE stocks")
        
        return all_stocks
    
    def get_bse_stocks(self, force_refresh=False):
        """
        Get complete list of BSE stocks
        """
        cache_file = self.cache_dir / "bse_stocks.json"
        
        # Try to load from cache
        if not force_refresh and self._is_cache_valid(cache_file):
            cached_data = self._load_cache(cache_file)
            if cached_data:
                print(f"Loaded {len(cached_data)} BSE stocks from cache")
                return cached_data
        
        # Fetch from Finnhub
        print("Fetching BSE stocks from Finnhub API...")
        all_stocks = []
        
        try:
            url = f"https://finnhub.io/api/v1/stock/symbol?exchange=BSE&token={self.finnhub_key}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                stocks = response.json()
                
                for stock in stocks:
                    symbol = stock.get('symbol', '')
                    all_stocks.append({
                        'symbol': symbol,
                        'name': stock.get('description', ''),
                        'type': stock.get('type', 'Common Stock'),
                        'currency': 'INR',
                        'market': 'India (BSE)',
                        'bse_symbol': symbol.replace('.BO', '')
                    })
                
                print(f"Fetched {len(all_stocks)} stocks from BSE")
        except Exception as e:
            print(f"Error fetching BSE stocks: {e}")
        
        # Save to cache
        if all_stocks:
            self._save_cache(cache_file, all_stocks)
            print(f"Cached {len(all_stocks)} BSE stocks")
        
        return all_stocks
    
    def get_all_stocks(self, force_refresh=False):
        """
        Get ALL stocks from US, NSE, and BSE
        """
        all_stocks = {
            'us': self.get_us_stocks(force_refresh),
            'nse': self.get_nse_stocks(force_refresh),
            'bse': self.get_bse_stocks(force_refresh)
        }
        
        total = sum(len(stocks) for stocks in all_stocks.values())
        print(f"\nTotal stocks available: {total}")
        print(f"  - US: {len(all_stocks['us'])}")
        print(f"  - NSE: {len(all_stocks['nse'])}")
        print(f"  - BSE: {len(all_stocks['bse'])}")
        
        return all_stocks
    
    def search_cached_stocks(self, query, market='all'):
        """
        Search through cached stock lists (offline search)
        Supports both lowercase and uppercase, searches by company name
        """
        # Normalize query to lowercase for case-insensitive search
        query_lower = query.lower().strip()
        results = []
        seen_symbols = set()
        
        def matches_stock(stock, query_lower):
            """Check if stock matches the query (case-insensitive)"""
            symbol_lower = stock['symbol'].lower()
            name_lower = stock['name'].lower()
            
            # Direct match in symbol or name
            if query_lower in symbol_lower or query_lower in name_lower:
                return True
            
            # Check if query matches any word in the company name
            name_words = name_lower.split()
            for word in name_words:
                if word.startswith(query_lower) or query_lower in word:
                    return True
            
            return False
        
        # Load appropriate market
        if market in ['all', 'us']:
            us_stocks = self.get_us_stocks()
            for stock in us_stocks:
                if stock['symbol'] not in seen_symbols and matches_stock(stock, query_lower):
                    results.append(stock)
                    seen_symbols.add(stock['symbol'])
        
        if market in ['all', 'india', 'nse']:
            nse_stocks = self.get_nse_stocks()
            for stock in nse_stocks:
                if stock['symbol'] not in seen_symbols and matches_stock(stock, query_lower):
                    results.append(stock)
                    seen_symbols.add(stock['symbol'])
        
        if market in ['all', 'india', 'bse']:
            bse_stocks = self.get_bse_stocks()
            for stock in bse_stocks:
                if stock['symbol'] not in seen_symbols and matches_stock(stock, query_lower):
                    results.append(stock)
                    seen_symbols.add(stock['symbol'])
        
        # Sort results: exact matches first, then partial matches
        def sort_key(stock):
            symbol_lower = stock['symbol'].lower()
            name_lower = stock['name'].lower()
            
            # Exact symbol match gets highest priority
            if symbol_lower == query_lower:
                return (0, stock['symbol'])
            # Symbol starts with query
            elif symbol_lower.startswith(query_lower):
                return (1, stock['symbol'])
            # Company name starts with query
            elif name_lower.startswith(query_lower):
                return (2, stock['name'])
            # Contains in symbol
            elif query_lower in symbol_lower:
                return (3, stock['symbol'])
            # Contains in name
            else:
                return (4, stock['name'])
        
        results.sort(key=sort_key)
        
        return results[:50]  # Return top 50 matches
    
    def get_cache_info(self):
        """
        Get information about cached data
        """
        info = {}
        
        for market in ['us_stocks', 'nse_stocks', 'bse_stocks']:
            cache_file = self.cache_dir / f"{market}.json"
            
            if cache_file.exists():
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age = datetime.now() - file_time
                
                cached_data = self._load_cache(cache_file)
                count = len(cached_data) if cached_data else 0
                
                info[market] = {
                    'exists': True,
                    'count': count,
                    'last_updated': file_time.isoformat(),
                    'age_hours': round(age.total_seconds() / 3600, 2),
                    'is_valid': age.total_seconds() < self.cache_duration
                }
            else:
                info[market] = {
                    'exists': False,
                    'count': 0,
                    'last_updated': None,
                    'age_hours': None,
                    'is_valid': False
                }
        
        return info
