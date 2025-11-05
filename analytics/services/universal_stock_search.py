import requests
import yfinance as yf
from datetime import datetime

class UniversalStockSearch:
    def __init__(self, finnhub_api_key=None):
        """
        Universal stock search service using Finnhub API
        """
        self.finnhub_key = finnhub_api_key or "d43h6l1r01qvk0jbscngd43h6l1r01qvk0jbsco0"
    
    def search_all_stocks(self, query, limit=20, filter_markets=True):
        """
        Search for stocks using Finnhub symbol search
        By default filters to US and Indian markets only
        """
        results = []
        
        try:
            # Use Finnhub's symbol search API
            url = f"https://finnhub.io/api/v1/search?q={query}&token={self.finnhub_key}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'result' in data:
                    for item in data['result']:
                        symbol = item.get('symbol', '')
                        description = item.get('description', '')
                        stock_type = item.get('type', '')
                        
                        # Determine market
                        market = None
                        is_us_or_indian = False
                        
                        if '.NS' in symbol or symbol.startswith('NSE:'):
                            market = 'India (NSE)'
                            is_us_or_indian = True
                        elif '.BO' in symbol or symbol.startswith('BSE:'):
                            market = 'India (BSE)'
                            is_us_or_indian = True
                        elif '.L' in symbol or symbol.startswith('LSE:'):
                            market = 'UK (LSE)'
                        elif '.TO' in symbol or symbol.startswith('TSE:'):
                            market = 'Canada (TSX)'
                        elif '.HK' in symbol or '.HKG' in symbol:
                            market = 'Hong Kong'
                        elif '.SS' in symbol or '.SZ' in symbol:
                            market = 'China'
                        elif '.TW' in symbol or '.TWO' in symbol:
                            market = 'Taiwan'
                        else:
                            # Assume US if no other market identifier
                            market = 'US'
                            is_us_or_indian = True
                        
                        # Filter to only US and Indian markets by default
                        if filter_markets and not is_us_or_indian:
                            continue
                        
                        results.append({
                            'symbol': symbol,
                            'name': description,
                            'type': stock_type,
                            'market': market
                        })
                        
                        if len(results) >= limit:
                            break
        except Exception as e:
            print(f"Finnhub search error: {e}")
        
        return results
    
    def search_us_stocks(self, query, limit=20):
        """
        Search specifically for US stocks
        """
        results = []
        
        try:
            # Use Finnhub's symbol search with US filter
            url = f"https://finnhub.io/api/v1/search?q={query}&exchange=US&token={self.finnhub_key}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'result' in data:
                    for item in data['result'][:limit]:
                        results.append({
                            'symbol': item.get('symbol', ''),
                            'name': item.get('description', ''),
                            'type': item.get('type', 'Common Stock'),
                            'market': 'US'
                        })
        except Exception as e:
            print(f"US stock search error: {e}")
        
        return results
    
    def search_indian_stocks(self, query, limit=20):
        """
        Search specifically for Indian stocks (NSE/BSE)
        """
        results = []
        
        try:
            # Method 1: Try direct NSE symbol lookup with yfinance
            possible_symbols = [
                f"{query.upper()}.NS",
                f"{query.upper()}.BO"
            ]
            
            for symbol in possible_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    if info and info.get('symbol'):
                        results.append({
                            'symbol': symbol,
                            'name': info.get('longName', info.get('shortName', query)),
                            'type': 'Common Stock',
                            'market': 'India (NSE)' if '.NS' in symbol else 'India (BSE)',
                            'currency': 'INR'
                        })
                except:
                    continue
            
            # Method 2: Use Finnhub to search Indian exchanges
            try:
                url = f"https://finnhub.io/api/v1/search?q={query}&token={self.finnhub_key}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'result' in data:
                        for item in data['result']:
                            symbol = item.get('symbol', '')
                            
                            # Filter only Indian stocks
                            if '.NS' in symbol or '.BO' in symbol or symbol.startswith('NSE:') or symbol.startswith('BSE:'):
                                results.append({
                                    'symbol': symbol,
                                    'name': item.get('description', ''),
                                    'type': item.get('type', 'Common Stock'),
                                    'market': 'India (NSE)' if '.NS' in symbol or symbol.startswith('NSE:') else 'India (BSE)'
                                })
            except:
                pass
            
        except Exception as e:
            print(f"Indian stock search error: {e}")
        
        # Remove duplicates
        seen = set()
        unique_results = []
        for item in results:
            if item['symbol'] not in seen:
                seen.add(item['symbol'])
                unique_results.append(item)
        
        return unique_results[:limit]
    
    def get_stock_exchanges(self):
        """
        Get list of supported exchanges
        """
        try:
            url = f"https://finnhub.io/api/v1/stock/exchange?token={self.finnhub_key}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching exchanges: {e}")
        
        return []
    
    def search_by_exchange(self, query, exchange='US', limit=20):
        """
        Search stocks by specific exchange
        Supported exchanges: US, NSE, BSE, LSE, TSX, HKEX, etc.
        """
        results = []
        
        try:
            url = f"https://finnhub.io/api/v1/search?q={query}&exchange={exchange}&token={self.finnhub_key}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'result' in data:
                    for item in data['result'][:limit]:
                        results.append({
                            'symbol': item.get('symbol', ''),
                            'name': item.get('description', ''),
                            'type': item.get('type', ''),
                            'market': exchange
                        })
        except Exception as e:
            print(f"Exchange search error: {e}")
        
        return results
