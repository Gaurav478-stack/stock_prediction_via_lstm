import yfinance as yf
from datetime import datetime, timedelta
import requests
import time
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import hashlib

class NewsService:
    def __init__(self):
        # API Keys
        self.newsapi_key = '01e4e1ebea9747de8249693942b662cc'
        self.finnhub_key = 'd43h6l1r01qvk0jbscngd43h6l1r01qvk0jbsco0'
        
        # API Endpoints
        self.newsapi_url = 'https://newsapi.org/v2'
        self.finnhub_url = 'https://finnhub.io/api/v1'
        
        # Cache for news articles (in-memory cache)
        self._cache = {}
        self._cache_duration = 300  # 5 minutes cache
        
        # RSS Feed URLs for Indian financial news
        self.indian_rss_feeds = {
            'moneycontrol': 'https://www.moneycontrol.com/rss/latestnews.xml',
            'economictimes': 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
            'businessstandard': 'https://www.business-standard.com/rss/markets-101.rss',
            'ndtvprofit': 'https://feeds.feedburner.com/ndtvprofit-latest'
        }
        
        # RSS Feed URLs for US financial news
        self.us_rss_feeds = {
            'bloomberg_markets': 'https://feeds.bloomberg.com/markets/news.rss',
            'reuters_business': 'http://feeds.reuters.com/reuters/businessNews',
            'wsj_markets': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
            'cnbc_top_business': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147',
            'cnbc_market_insider': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20409666',
            'yahoo_finance': 'https://finance.yahoo.com/news/rssindex',
            'marketwatch': 'http://feeds.marketwatch.com/marketwatch/topstories/',
            'investors_business_daily': 'https://www.investors.com/feed/',
            'seeking_alpha': 'https://seekingalpha.com/market_currents.xml',
            'financial_times_us': 'https://www.ft.com/?format=rss',
            'forbes_money': 'https://www.forbes.com/money/feed2/',
            'barrons': 'https://www.barrons.com/news/rss'
        }
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        key_str = f"{prefix}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str):
        """Get data from cache if not expired"""
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_duration:
                return cached_data
        return None
    
    def _set_cache(self, cache_key: str, data):
        """Store data in cache with timestamp"""
        self._cache[cache_key] = (data, time.time())
    
    def get_general_news(self, limit: int = 10, region: str = 'us') -> list:
        """Get general financial news from multiple sources with caching"""
        # Check cache first
        cache_key = self._get_cache_key('general_news', limit=limit, region=region)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            print(f"DEBUG: Returning {len(cached_result)} articles from cache")
            return cached_result
        
        try:
            all_news = []
            
            # Try NewsAPI first (best for general news)
            try:
                newsapi_news = self._fetch_newsapi_general(limit=limit, region=region)
                if newsapi_news:
                    all_news.extend(newsapi_news)
                    print(f"DEBUG: Got {len(newsapi_news)} articles from NewsAPI")
            except Exception as e:
                print(f"NewsAPI error: {e}")
            
            # Fetch RSS feeds based on region
            try:
                rss_news = self._fetch_rss_feeds(limit=limit, region=region)
                if rss_news:
                    all_news.extend(rss_news)
                    print(f"DEBUG: Got {len(rss_news)} articles from RSS feeds ({region.upper()} region)")
            except Exception as e:
                print(f"RSS feeds error: {e}")
            
            # Try Finnhub as additional source (US market focus)
            if region == 'us' and len(all_news) < limit:
                try:
                    finnhub_news = self._fetch_finnhub_general(limit=limit - len(all_news))
                    if finnhub_news:
                        all_news.extend(finnhub_news)
                        print(f"DEBUG: Got {len(finnhub_news)} articles from Finnhub")
                except Exception as e:
                    print(f"Finnhub error: {e}")
            
            # Fallback to yfinance
            if len(all_news) < 3:
                try:
                    yf_news = self._fetch_yfinance_general(limit=limit)
                    if yf_news:
                        all_news.extend(yf_news)
                        print(f"DEBUG: Got {len(yf_news)} articles from yfinance")
                except Exception as e:
                    print(f"yfinance error: {e}")
            
            # Remove duplicates based on title
            seen_titles = set()
            unique_news = []
            for item in all_news:
                title_lower = item['title'].lower()
                if title_lower not in seen_titles:
                    seen_titles.add(title_lower)
                    unique_news.append(item)
            
            # Sort by published date (newest first)
            unique_news.sort(key=lambda x: x['publishedAt'], reverse=True)
            
            # Return requested number of articles
            result = unique_news[:limit]
            
            if len(result) == 0:
                print("DEBUG: No news from any source, using mock data")
                result = self._get_mock_news(limit)
            else:
                print(f"DEBUG: Returning {len(result)} unique news items")
            
            # Cache the result
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            print(f"Error fetching general news: {e}")
            import traceback
            traceback.print_exc()
            return self._get_mock_news(limit)
    
    def get_stock_news(self, symbol: str, limit: int = 10) -> list:
        """Get news for a specific stock from multiple sources"""
        try:
            all_news = []
            
            # Try Finnhub first for stock-specific news (best for individual stocks)
            try:
                finnhub_news = self._fetch_finnhub_stock_news(symbol, limit=limit)
                if finnhub_news:
                    all_news.extend(finnhub_news)
                    print(f"DEBUG: Got {len(finnhub_news)} articles from Finnhub for {symbol}")
            except Exception as e:
                print(f"Finnhub stock news error: {e}")
            
            # Try NewsAPI for additional coverage
            if len(all_news) < limit:
                try:
                    newsapi_news = self._fetch_newsapi_stock_news(symbol, limit=limit - len(all_news))
                    if newsapi_news:
                        all_news.extend(newsapi_news)
                        print(f"DEBUG: Got {len(newsapi_news)} articles from NewsAPI for {symbol}")
                except Exception as e:
                    print(f"NewsAPI stock news error: {e}")
            
            # Fallback to yfinance
            if len(all_news) < 3:
                try:
                    yf_news = self._fetch_yfinance_stock_news(symbol, limit=limit)
                    if yf_news:
                        all_news.extend(yf_news)
                        print(f"DEBUG: Got {len(yf_news)} articles from yfinance for {symbol}")
                except Exception as e:
                    print(f"yfinance stock news error: {e}")
            
            # Remove duplicates
            seen_titles = set()
            unique_news = []
            for item in all_news:
                title_lower = item['title'].lower()
                if title_lower not in seen_titles:
                    seen_titles.add(title_lower)
                    unique_news.append(item)
            
            # Sort by date
            unique_news.sort(key=lambda x: x['publishedAt'], reverse=True)
            result = unique_news[:limit]
            
            if len(result) == 0:
                return self._get_mock_stock_news(symbol, limit)
            
            return result
        except Exception as e:
            print(f"Error fetching news for {symbol}: {e}")
            return self._get_mock_stock_news(symbol, limit)
    
    # ========== RSS Feed Methods ==========
    def _fetch_single_rss_feed(self, source_name: str, feed_url: str) -> list:
        """Fetch and parse a single RSS feed"""
        try:
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                print(f"No entries from {source_name}")
                return []
            
            news_items = []
            # Process each entry (up to 5 per feed)
            for entry in feed.entries[:5]:
                # Parse published date
                published_at = datetime.now().isoformat()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_at = datetime(*entry.published_parsed[:6]).isoformat()
                    except:
                        pass
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    try:
                        published_at = datetime(*entry.updated_parsed[:6]).isoformat()
                    except:
                        pass
                
                # Extract thumbnail if available
                thumbnail = ''
                if hasattr(entry, 'media_content') and entry.media_content:
                    thumbnail = entry.media_content[0].get('url', '')
                elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                    thumbnail = entry.media_thumbnail[0].get('url', '')
                elif hasattr(entry, 'enclosures') and entry.enclosures:
                    for enclosure in entry.enclosures:
                        if 'image' in enclosure.get('type', ''):
                            thumbnail = enclosure.get('href', '')
                            break
                
                # Format the news item
                news_item = {
                    'title': entry.get('title', 'No title'),
                    'publisher': source_name.title().replace('_', ' '),
                    'link': entry.get('link', '#'),
                    'publishedAt': published_at,
                    'thumbnail': thumbnail,
                    'relatedTickers': []
                }
                
                news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            print(f"Error fetching RSS from {source_name}: {e}")
            return []
    
    def _fetch_rss_feeds(self, limit: int = 10, region: str = 'in') -> list:
        """Fetch news from financial RSS feeds using parallel requests"""
        try:
            # Select RSS feeds based on region
            rss_feeds = self.indian_rss_feeds if region == 'in' else self.us_rss_feeds
            
            all_rss_news = []
            
            # Use ThreadPoolExecutor for parallel fetching (max 5 concurrent requests)
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all feed fetch tasks
                future_to_feed = {
                    executor.submit(self._fetch_single_rss_feed, source_name, feed_url): source_name
                    for source_name, feed_url in rss_feeds.items()
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_feed, timeout=10):
                    try:
                        feed_news = future.result(timeout=5)
                        if feed_news:
                            all_rss_news.extend(feed_news)
                    except Exception as e:
                        source_name = future_to_feed[future]
                        print(f"Error fetching {source_name}: {e}")
            
            # Sort by published date (newest first)
            all_rss_news.sort(key=lambda x: x['publishedAt'], reverse=True)
            
            return all_rss_news[:limit]
            
        except Exception as e:
            print(f"Error fetching RSS feeds: {e}")
            return []
    
    # ========== NewsAPI Methods ==========
    def _fetch_newsapi_general(self, limit: int = 10, region: str = 'us') -> list:
        """Fetch general financial news from NewsAPI"""
        try:
            # Choose sources based on region
            if region == 'in':
                # Indian financial sources with market-specific query
                sources = 'the-times-of-india,the-hindu,financial-express'
                query = 'sensex nifty stock market'
                params = {
                    'apiKey': self.newsapi_key,
                    'q': query,
                    'sources': sources,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': limit
                }
                endpoint = f'{self.newsapi_url}/everything'
            else:
                # US financial news
                params = {
                    'apiKey': self.newsapi_key,
                    'q': 'stock market OR finance OR economy OR trading',
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': limit
                }
                endpoint = f'{self.newsapi_url}/everything'
            
            response = requests.get(endpoint, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
            
            articles = data.get('articles', [])
            formatted_news = []
            
            for article in articles:
                formatted_news.append({
                    'title': article.get('title', 'No title'),
                    'publisher': article.get('source', {}).get('name', 'Unknown'),
                    'link': article.get('url', '#'),
                    'publishedAt': article.get('publishedAt', datetime.now().isoformat()),
                    'thumbnail': article.get('urlToImage', ''),
                    'relatedTickers': []
                })
            
            return formatted_news
        except Exception as e:
            print(f"Error fetching NewsAPI general news: {e}")
            return []
    
    def _fetch_newsapi_stock_news(self, symbol: str, limit: int = 10) -> list:
        """Fetch stock-specific news from NewsAPI"""
        try:
            # Remove exchange suffix for search (e.g., .NS for NSE)
            search_symbol = symbol.split('.')[0]
            
            params = {
                'apiKey': self.newsapi_key,
                'q': f'{search_symbol} stock',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': limit
            }
            
            response = requests.get(f'{self.newsapi_url}/everything', params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                return []
            
            articles = data.get('articles', [])
            formatted_news = []
            
            for article in articles:
                formatted_news.append({
                    'title': article.get('title', 'No title'),
                    'publisher': article.get('source', {}).get('name', 'Unknown'),
                    'link': article.get('url', '#'),
                    'publishedAt': article.get('publishedAt', datetime.now().isoformat()),
                    'thumbnail': article.get('urlToImage', ''),
                    'symbol': symbol
                })
            
            return formatted_news
        except Exception as e:
            print(f"Error fetching NewsAPI stock news: {e}")
            return []
    
    # ========== Finnhub Methods ==========
    def _fetch_finnhub_general(self, limit: int = 10) -> list:
        """Fetch general market news from Finnhub"""
        try:
            params = {
                'category': 'general',
                'token': self.finnhub_key
            }
            
            response = requests.get(f'{self.finnhub_url}/news', params=params, timeout=5)
            response.raise_for_status()
            articles = response.json()
            
            formatted_news = []
            for article in articles[:limit]:
                formatted_news.append({
                    'title': article.get('headline', 'No title'),
                    'publisher': article.get('source', 'Finnhub'),
                    'link': article.get('url', '#'),
                    'publishedAt': datetime.fromtimestamp(article.get('datetime', time.time())).isoformat(),
                    'thumbnail': article.get('image', ''),
                    'relatedTickers': article.get('related', '').split(',') if article.get('related') else []
                })
            
            return formatted_news
        except Exception as e:
            print(f"Error fetching Finnhub general news: {e}")
            return []
    
    def _fetch_finnhub_stock_news(self, symbol: str, limit: int = 10) -> list:
        """Fetch stock-specific news from Finnhub"""
        try:
            # Remove exchange suffix for Finnhub
            finnhub_symbol = symbol.replace('.NS', '').replace('.BO', '')
            
            # Calculate date range (last 7 days)
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            params = {
                'symbol': finnhub_symbol,
                'from': from_date,
                'to': to_date,
                'token': self.finnhub_key
            }
            
            response = requests.get(f'{self.finnhub_url}/company-news', params=params, timeout=5)
            response.raise_for_status()
            articles = response.json()
            
            formatted_news = []
            for article in articles[:limit]:
                formatted_news.append({
                    'title': article.get('headline', 'No title'),
                    'publisher': article.get('source', 'Finnhub'),
                    'link': article.get('url', '#'),
                    'publishedAt': datetime.fromtimestamp(article.get('datetime', time.time())).isoformat(),
                    'thumbnail': article.get('image', ''),
                    'symbol': symbol
                })
            
            return formatted_news
        except Exception as e:
            print(f"Error fetching Finnhub stock news: {e}")
            return []
    
    # ========== yfinance Fallback Methods ==========
    def _fetch_yfinance_general(self, limit: int = 10) -> list:
        """Fetch general news using yfinance as fallback"""
        try:
            ticker = yf.Ticker("SPY")
            news = ticker.news
            
            if not news:
                return []
            
            formatted_news = []
            for item in news[:limit]:
                title = item.get('title', '')
                publisher = item.get('publisher', '')
                
                if not title or not publisher:
                    continue
                
                formatted_news.append({
                    'title': title,
                    'publisher': publisher,
                    'link': item.get('link', '#'),
                    'publishedAt': datetime.fromtimestamp(item.get('providerPublishTime', 0)).isoformat() if item.get('providerPublishTime') else datetime.now().isoformat(),
                    'thumbnail': item.get('thumbnail', {}).get('resolutions', [{}])[0].get('url', '') if item.get('thumbnail') else '',
                    'relatedTickers': item.get('relatedTickers', [])
                })
            
            return formatted_news
        except Exception as e:
            print(f"Error fetching yfinance general news: {e}")
            return []
    
    def _fetch_yfinance_stock_news(self, symbol: str, limit: int = 10) -> list:
        """Fetch stock-specific news using yfinance as fallback"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return []
            
            formatted_news = []
            for item in news[:limit]:
                formatted_news.append({
                    'title': item.get('title', 'No title'),
                    'publisher': item.get('publisher', 'Unknown'),
                    'link': item.get('link', '#'),
                    'publishedAt': datetime.fromtimestamp(item.get('providerPublishTime', 0)).isoformat() if item.get('providerPublishTime') else datetime.now().isoformat(),
                    'thumbnail': item.get('thumbnail', {}).get('resolutions', [{}])[0].get('url', '') if item.get('thumbnail') else '',
                    'symbol': symbol
                })
            
            return formatted_news
        except Exception as e:
            print(f"Error fetching yfinance stock news: {e}")
            return []
    
    # Deprecated methods - kept for backwards compatibility
    def _fetch_yahoo_news(self, symbol: str = None, limit: int = 10) -> list:
        """Deprecated: Use _fetch_yfinance_general or _fetch_yfinance_stock_news"""
        return self._fetch_yfinance_general(limit) if not symbol else self._fetch_yfinance_stock_news(symbol, limit)
    
    def _fetch_yfinance_news(self, symbol: str, limit: int = 10) -> list:
        """Deprecated: Use _fetch_yfinance_stock_news"""
        return self._fetch_yfinance_stock_news(symbol, limit)
    
    def _fetch_newsapi_news(self, symbol: str = None, limit: int = 10) -> list:
        """Deprecated: Use _fetch_newsapi_general or _fetch_newsapi_stock_news"""
        return self._fetch_newsapi_general(limit) if not symbol else self._fetch_newsapi_stock_news(symbol, limit)
    
    def _fetch_finnhub_news(self, symbol: str = None, limit: int = 10) -> list:
        """Deprecated: Use _fetch_finnhub_general or _fetch_finnhub_stock_news"""
        return self._fetch_finnhub_general(limit) if not symbol else self._fetch_finnhub_stock_news(symbol, limit)
    
    def _get_mock_news(self, limit: int = 10) -> list:
        """Return mock news data"""
        base_time = datetime.now()
        mock_news = [
            {
                'title': 'Stock Market Reaches New Heights Amid Economic Recovery',
                'publisher': 'Financial Times',
                'link': '#',
                'publishedAt': (base_time - timedelta(hours=2)).isoformat(),
                'thumbnail': '',
                'relatedTickers': ['SPY', 'QQQ']
            },
            {
                'title': 'Tech Sector Leads Market Rally as Investors Eye AI Growth',
                'publisher': 'Bloomberg',
                'link': '#',
                'publishedAt': (base_time - timedelta(hours=4)).isoformat(),
                'thumbnail': '',
                'relatedTickers': ['MSFT', 'GOOGL', 'NVDA']
            },
            {
                'title': 'Federal Reserve Signals Steady Interest Rate Policy',
                'publisher': 'Reuters',
                'link': '#',
                'publishedAt': (base_time - timedelta(hours=6)).isoformat(),
                'thumbnail': '',
                'relatedTickers': []
            },
            {
                'title': 'Energy Stocks Surge on Rising Oil Prices',
                'publisher': 'CNBC',
                'link': '#',
                'publishedAt': (base_time - timedelta(hours=8)).isoformat(),
                'thumbnail': '',
                'relatedTickers': ['XOM', 'CVX']
            },
            {
                'title': 'Consumer Confidence Index Shows Strong Growth',
                'publisher': 'Wall Street Journal',
                'link': '#',
                'publishedAt': (base_time - timedelta(hours=10)).isoformat(),
                'thumbnail': '',
                'relatedTickers': ['WMT', 'TGT']
            }
        ]
        return mock_news[:limit]
    
    def _get_mock_stock_news(self, symbol: str, limit: int = 10) -> list:
        """Return mock news data for a specific stock"""
        base_time = datetime.now()
        mock_news = [
            {
                'title': f'{symbol} Reports Strong Quarterly Earnings',
                'publisher': 'MarketWatch',
                'link': '#',
                'publishedAt': (base_time - timedelta(hours=3)).isoformat(),
                'thumbnail': '',
                'symbol': symbol
            },
            {
                'title': f'Analysts Upgrade {symbol} Stock Rating',
                'publisher': 'Seeking Alpha',
                'link': '#',
                'publishedAt': (base_time - timedelta(hours=5)).isoformat(),
                'thumbnail': '',
                'symbol': symbol
            },
            {
                'title': f'{symbol} Announces New Product Launch',
                'publisher': 'TechCrunch',
                'link': '#',
                'publishedAt': (base_time - timedelta(hours=7)).isoformat(),
                'thumbnail': '',
                'symbol': symbol
            }
        ]
        return mock_news[:limit]
