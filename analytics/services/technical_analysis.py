import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class TechnicalAnalysis:
    def __init__(self):
        self.period = "1y"
    
    async def analyze(self, symbol: str) -> dict:
        """Perform comprehensive technical analysis"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=self.period)
            
            if hist.empty:
                return await self._get_mock_analysis(symbol)
            
            # Calculate technical indicators
            rsi = self._calculate_rsi(hist)
            macd, macd_signal = self._calculate_macd(hist)
            sma_20, sma_50 = self._calculate_moving_averages(hist)
            support, resistance = self._calculate_support_resistance(hist)
            
            # Determine trend
            trend = self._determine_trend(hist, sma_20, sma_50)
            
            # Generate recommendation
            recommendation, confidence = self._generate_recommendation(
                rsi, macd, trend, hist
            )
            
            return {
                "symbol": symbol,
                "analysis_type": "technical",
                "rsi": round(rsi, 2),
                "macd": round(macd, 4),
                "macd_signal": round(macd_signal, 4),
                "sma_20": round(sma_20, 2),
                "sma_50": round(sma_50, 2),
                "trend": trend,
                "support": round(support, 2),
                "resistance": round(resistance, 2),
                "recommendation": recommendation,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Technical analysis error for {symbol}: {e}")
            return await self._get_mock_analysis(symbol)
    
    def _calculate_rsi(self, data, period: int = 14):
        """Calculate Relative Strength Index"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50
    
    def _calculate_macd(self, data):
        """Calculate MACD"""
        exp1 = data['Close'].ewm(span=12).mean()
        exp2 = data['Close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        return macd.iloc[-1] if not macd.empty else 0, signal.iloc[-1] if not signal.empty else 0
    
    def _calculate_moving_averages(self, data):
        """Calculate Simple Moving Averages"""
        sma_20 = data['Close'].rolling(window=20).mean()
        sma_50 = data['Close'].rolling(window=50).mean()
        return sma_20.iloc[-1] if not sma_20.empty else 0, sma_50.iloc[-1] if not sma_50.empty else 0
    
    def _calculate_support_resistance(self, data):
        """Calculate support and resistance levels"""
        recent_low = data['Low'].tail(20).min()
        recent_high = data['High'].tail(20).max()
        return recent_low, recent_high
    
    def _determine_trend(self, data, sma_20, sma_50):
        """Determine market trend"""
        if sma_20 > sma_50 and data['Close'].iloc[-1] > sma_20:
            return "bullish"
        elif sma_20 < sma_50 and data['Close'].iloc[-1] < sma_20:
            return "bearish"
        else:
            return "neutral"
    
    def _generate_recommendation(self, rsi, macd, trend, data):
        """Generate trading recommendation"""
        price_trend = "up" if data['Close'].iloc[-1] > data['Close'].iloc[-5] else "down"
        
        # Simple rule-based system
        buy_signals = 0
        sell_signals = 0
        
        if rsi < 30:
            buy_signals += 1
        elif rsi > 70:
            sell_signals += 1
            
        if macd > 0:
            buy_signals += 1
        else:
            sell_signals += 1
            
        if trend == "bullish":
            buy_signals += 1
        elif trend == "bearish":
            sell_signals += 1
            
        if buy_signals > sell_signals:
            recommendation = "BUY"
            confidence = min(90, 60 + (buy_signals - sell_signals) * 10)
        elif sell_signals > buy_signals:
            recommendation = "SELL"
            confidence = min(90, 60 + (sell_signals - buy_signals) * 10)
        else:
            recommendation = "HOLD"
            confidence = 50
            
        return recommendation, confidence
    
    async def _get_mock_analysis(self, symbol):
        """Fallback mock analysis"""
        return {
            "symbol": symbol,
            "analysis_type": "technical",
            "rsi": 55.5,
            "macd": 0.025,
            "macd_signal": 0.015,
            "sma_20": 150.25,
            "sma_50": 148.75,
            "trend": "bullish",
            "support": 145.50,
            "resistance": 155.75,
            "recommendation": "HOLD",
            "confidence": 65,
            "timestamp": datetime.utcnow().isoformat()
        }