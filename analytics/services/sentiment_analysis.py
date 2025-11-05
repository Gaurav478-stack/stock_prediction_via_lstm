import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from textblob import TextBlob
import re
from typing import Dict, List, Optional
import asyncio
import aiohttp

class SentimentAnalysis:
    def __init__(self):
        self.news_sources = [
            'bloomberg', 'reuters', 'financial-times', 
            'cnbc', 'marketwatch', 'yahoo-finance'
        ]
        self.sentiment_cache = {}
    
    async def analyze_stock_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """
        Perform comprehensive sentiment analysis for a stock
        """
        try:
            # Get news articles
            news_articles = await self._fetch_news_articles(symbol, days)
            
            if not news_articles:
                return await self._get_mock_sentiment(symbol)
            
            # Analyze sentiment for each article
            sentiment_scores = []
            article_analyses = []
            
            for article in news_articles:
                analysis = self._analyze_article_sentiment(article)
                sentiment_scores.append(analysis['sentiment_score'])
                article_analyses.append(analysis)
            
            # Calculate overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(sentiment_scores, article_analyses)
            
            return {
                "symbol": symbol,
                "analysis_type": "sentiment",
                "overall_sentiment": overall_sentiment['sentiment'],
                "sentiment_score": overall_sentiment['score'],
                "confidence": overall_sentiment['confidence'],
                "total_articles": len(news_articles),
                "positive_articles": overall_sentiment['positive_count'],
                "negative_articles": overall_sentiment['negative_count'],
                "neutral_articles": overall_sentiment['neutral_count'],
                "recent_trend": overall_sentiment['trend'],
                "key_topics": self._extract_key_topics(article_analyses),
                "article_analyses": article_analyses[:5],  # Top 5 articles
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Sentiment analysis error for {symbol}: {e}")
            return await self._get_mock_sentiment(symbol)
    
    async def _fetch_news_articles(self, symbol: str, days: int) -> List[Dict]:
        """
        Fetch recent news articles for a stock symbol
        In production, this would use a news API like NewsAPI, Alpha Vantage News, etc.
        """
        try:
            # Mock implementation - in production, replace with actual news API
            mock_articles = self._generate_mock_articles(symbol, days)
            return mock_articles
            
        except Exception as e:
            print(f"Error fetching news articles: {e}")
            return []
    
    def _analyze_article_sentiment(self, article: Dict) -> Dict:
        """
        Analyze sentiment of a single news article
        """
        try:
            # Combine title and description for analysis
            text = f"{article.get('title', '')} {article.get('description', '')}"
            
            # Clean text
            text = self._clean_text(text)
            
            if not text:
                return {
                    "title": article.get('title', ''),
                    "sentiment_score": 0,
                    "sentiment": "neutral",
                    "confidence": 0,
                    "keywords": []
                }
            
            # Perform sentiment analysis
            blob = TextBlob(text)
            sentiment_score = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Determine sentiment category
            if sentiment_score > 0.1:
                sentiment = "positive"
                confidence = min(90, sentiment_score * 100 + subjectivity * 20)
            elif sentiment_score < -0.1:
                sentiment = "negative"
                confidence = min(90, abs(sentiment_score) * 100 + subjectivity * 20)
            else:
                sentiment = "neutral"
                confidence = min(80, (1 - abs(sentiment_score)) * 80)
            
            # Extract keywords
            keywords = self._extract_keywords(text)
            
            return {
                "title": article.get('title', ''),
                "source": article.get('source', ''),
                "published_at": article.get('published_at', ''),
                "sentiment_score": round(sentiment_score, 3),
                "sentiment": sentiment,
                "confidence": round(confidence),
                "subjectivity": round(subjectivity, 3),
                "keywords": keywords[:5]  # Top 5 keywords
            }
            
        except Exception as e:
            print(f"Error analyzing article sentiment: {e}")
            return {
                "title": article.get('title', ''),
                "sentiment_score": 0,
                "sentiment": "neutral",
                "confidence": 0,
                "keywords": []
            }
    
    def _calculate_overall_sentiment(self, sentiment_scores: List[float], article_analyses: List[Dict]) -> Dict:
        """
        Calculate overall sentiment from multiple articles
        """
        if not sentiment_scores:
            return {
                "sentiment": "neutral",
                "score": 0,
                "confidence": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "trend": "stable"
            }
        
        # Calculate weighted average sentiment
        weighted_scores = []
        for analysis in article_analyses:
            weight = analysis.get('confidence', 50) / 100
            weighted_scores.append(analysis['sentiment_score'] * weight)
        
        overall_score = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0
        
        # Count sentiment categories
        positive_count = sum(1 for a in article_analyses if a.get('sentiment') == 'positive')
        negative_count = sum(1 for a in article_analyses if a.get('sentiment') == 'negative')
        neutral_count = sum(1 for a in article_analyses if a.get('sentiment') == 'neutral')
        
        # Determine overall sentiment
        if overall_score > 0.1:
            sentiment = "bullish"
            confidence = min(95, (positive_count / len(article_analyses)) * 100 + overall_score * 50)
        elif overall_score < -0.1:
            sentiment = "bearish"
            confidence = min(95, (negative_count / len(article_analyses)) * 100 + abs(overall_score) * 50)
        else:
            sentiment = "neutral"
            confidence = min(85, (neutral_count / len(article_analyses)) * 100)
        
        # Determine trend (simple moving average of recent sentiments)
        recent_scores = sentiment_scores[-5:]  # Last 5 articles
        if len(recent_scores) >= 2:
            trend_score = np.mean(recent_scores) - np.mean(sentiment_scores)
            if trend_score > 0.05:
                trend = "improving"
            elif trend_score < -0.05:
                trend = "deteriorating"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return {
            "sentiment": sentiment,
            "score": round(overall_score, 3),
            "confidence": round(confidence),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "trend": trend
        }
    
    def _extract_key_topics(self, article_analyses: List[Dict]) -> List[str]:
        """
        Extract most frequently mentioned topics/keywords
        """
        all_keywords = []
        for analysis in article_analyses:
            all_keywords.extend(analysis.get('keywords', []))
        
        # Count keyword frequency
        keyword_freq = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Get top 5 most frequent keywords
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [keyword for keyword, count in top_keywords]
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and preprocess text for sentiment analysis
        """
        if not text:
            return ""
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from text
        """
        try:
            blob = TextBlob(text)
            
            # Get noun phrases as potential keywords
            keywords = []
            for np in blob.noun_phrases:
                if len(np.split()) <= 3:  # Limit to 3-word phrases
                    keywords.append(np)
            
            # Also include significant words (nouns, adjectives)
            pos_tags = blob.tags
            significant_words = [
                word for word, pos in pos_tags 
                if pos.startswith('NN') or pos.startswith('JJ')  # Nouns or adjectives
                and len(word) > 2  # Exclude very short words
            ]
            
            keywords.extend(significant_words)
            
            # Remove duplicates and return
            return list(set(keywords))
            
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []
    
    def _generate_mock_articles(self, symbol: str, days: int) -> List[Dict]:
        """
        Generate mock news articles for demonstration
        In production, replace with actual news API calls
        """
        base_date = datetime.utcnow()
        sources = ['Bloomberg', 'Reuters', 'CNBC', 'Financial Times', 'MarketWatch']
        
        # Different sentiment scenarios based on symbol (for demo purposes)
        sentiment_scenarios = {
            'AAPL': ['positive', 'positive', 'neutral', 'positive', 'negative'],
            'TSLA': ['negative', 'neutral', 'negative', 'positive', 'negative'],
            'MSFT': ['positive', 'positive', 'positive', 'neutral', 'positive'],
            'GOOGL': ['neutral', 'positive', 'neutral', 'positive', 'neutral'],
            'AMZN': ['positive', 'neutral', 'positive', 'negative', 'positive']
        }
        
        scenario = sentiment_scenarios.get(symbol, ['neutral'] * 5)
        
        articles = []
        for i in range(5):
            sentiment = scenario[i]
            
            if sentiment == 'positive':
                titles = [
                    f"{symbol} Surges on Strong Earnings Report",
                    f"Analysts Bullish on {symbol} Future Prospects",
                    f"{symbol} Announces Breakthrough Product Launch",
                    f"{symbol} Exceeds Market Expectations",
                    f"Investors Flock to {symbol} Amid Market Optimism"
                ]
                descriptions = [
                    f"Company demonstrates robust growth and market leadership",
                    f"Positive outlook driven by innovation and market position",
                    f"Strong performance metrics indicate continued success",
                    f"Market analysts upgrade ratings following impressive results",
                    f"Strategic initiatives paying off for shareholders"
                ]
            elif sentiment == 'negative':
                titles = [
                    f"{symbol} Faces Headwinds in Competitive Market",
                    f"Analysts Express Concerns Over {symbol} Performance",
                    f"{symbol} Reports Lower Than Expected Revenue",
                    f"Market Sentiment Cools on {symbol} Stock",
                    f"{symbol} Navigates Challenging Business Environment"
                ]
                descriptions = [
                    f"Company faces pressure from market conditions and competition",
                    f"Challenges in key markets impact financial performance",
                    f"Analysts cautious amid changing industry dynamics",
                    f"Stock underperforms relative to sector peers",
                    f"Management addresses concerns in investor meeting"
                ]
            else:  # neutral
                titles = [
                    f"{symbol} Maintains Steady Market Position",
                    f"Analysts Mixed on {symbol} Outlook",
                    f"{symbol} Reports In-Line With Expectations",
                    f"Market Watches {symbol} Next Moves",
                    f"{symbol} Navigates Evolving Market Landscape"
                ]
                descriptions = [
                    f"Company demonstrates stability in volatile market",
                    f"Performance metrics align with market expectations",
                    f"Balanced outlook with both opportunities and challenges",
                    f"Steady execution amid changing economic conditions",
                    f"Market awaits next catalyst for direction"
                ]
            
            articles.append({
                "title": titles[i],
                "description": descriptions[i],
                "source": sources[i],
                "published_at": (base_date - timedelta(days=i)).isoformat(),
                "url": f"https://example.com/news/{symbol.lower()}-{i}"
            })
        
        return articles
    
    async def _get_mock_sentiment(self, symbol: str) -> Dict:
        """
        Fallback mock sentiment analysis
        """
        # Simple sentiment based on symbol (for demo)
        sentiment_map = {
            'AAPL': {'sentiment': 'bullish', 'score': 0.4},
            'MSFT': {'sentiment': 'bullish', 'score': 0.35},
            'GOOGL': {'sentiment': 'neutral', 'score': 0.1},
            'AMZN': {'sentiment': 'bullish', 'score': 0.3},
            'TSLA': {'sentiment': 'bearish', 'score': -0.2}
        }
        
        default_sentiment = sentiment_map.get(symbol, {'sentiment': 'neutral', 'score': 0})
        
        return {
            "symbol": symbol,
            "analysis_type": "sentiment",
            "overall_sentiment": default_sentiment['sentiment'],
            "sentiment_score": default_sentiment['score'],
            "confidence": 75,
            "total_articles": 5,
            "positive_articles": 3,
            "negative_articles": 1,
            "neutral_articles": 1,
            "recent_trend": "stable",
            "key_topics": ["earnings", "market", "growth", "innovation"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_social_sentiment(self, symbol: str) -> Dict:
        """
        Analyze social media sentiment (placeholder for future implementation)
        """
        # This would integrate with Twitter API, Reddit API, etc.
        return {
            "symbol": symbol,
            "social_sentiment": "neutral",
            "social_score": 0.05,
            "mention_count": 150,
            "positive_mentions": 65,
            "negative_mentions": 45,
            "neutral_mentions": 40,
            "timestamp": datetime.utcnow().isoformat()
        }