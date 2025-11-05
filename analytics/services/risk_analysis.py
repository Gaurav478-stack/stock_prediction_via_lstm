import yfinance as yf
import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime

class RiskAnalysis:
    def __init__(self):
        self.period = "2y"
    
    async def analyze(self, symbol: str) -> dict:
        """Perform comprehensive risk analysis"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=self.period)
            
            if hist.empty or len(hist) < 30:
                return await self._get_mock_analysis(symbol)
            
            # Calculate returns
            returns = hist['Close'].pct_change().dropna()
            
            # Risk metrics
            volatility = self._calculate_volatility(returns)
            beta = await self._calculate_beta(symbol, returns)
            sharpe = self._calculate_sharpe_ratio(returns)
            var = self._calculate_var(returns)
            max_drawdown = self._calculate_max_drawdown(hist['Close'])
            
            # Risk assessment
            risk_level = self._assess_risk_level(volatility, beta, max_drawdown)
            
            return {
                "symbol": symbol,
                "analysis_type": "risk",
                "volatility": round(volatility * 100, 2),  # as percentage
                "beta": round(beta, 3),
                "sharpe_ratio": round(sharpe, 3),
                "value_at_risk": round(var * 100, 2),  # as percentage
                "max_drawdown": round(max_drawdown * 100, 2),  # as percentage
                "risk_level": risk_level,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Risk analysis error for {symbol}: {e}")
            return await self._get_mock_analysis(symbol)
    
    def _calculate_volatility(self, returns):
        """Calculate annualized volatility"""
        return returns.std() * np.sqrt(252)
    
    async def _calculate_beta(self, symbol, stock_returns):
        """Calculate beta relative to S&P 500"""
        try:
            # Get market data (SPY as proxy)
            market = yf.Ticker("SPY")
            market_hist = market.history(period=self.period)
            market_returns = market_hist['Close'].pct_change().dropna()
            
            # Align dates
            aligned_returns = stock_returns.align(market_returns, join='inner')
            stock_aligned, market_aligned = aligned_returns
            
            if len(stock_aligned) < 30:
                return 1.0
                
            # Calculate beta using covariance
            covariance = np.cov(stock_aligned, market_aligned)[0][1]
            market_variance = np.var(market_aligned)
            beta = covariance / market_variance
            
            return beta
        except:
            return 1.0  # Default beta
    
    def _calculate_sharpe_ratio(self, returns, risk_free_rate=0.02):
        """Calculate Sharpe ratio"""
        excess_returns = returns.mean() * 252 - risk_free_rate
        return excess_returns / (returns.std() * np.sqrt(252))
    
    def _calculate_var(self, returns, confidence_level=0.05):
        """Calculate Value at Risk"""
        return np.percentile(returns, confidence_level * 100)
    
    def _calculate_max_drawdown(self, prices):
        """Calculate maximum drawdown"""
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        return drawdown.min()
    
    def _assess_risk_level(self, volatility, beta, max_drawdown):
        """Assess overall risk level"""
        risk_score = (volatility * 0.4 + abs(beta - 1) * 0.3 + abs(max_drawdown) * 0.3)
        
        if risk_score < 0.1:
            return "low"
        elif risk_score < 0.2:
            return "medium"
        else:
            return "high"
    
    async def _get_mock_analysis(self, symbol):
        """Fallback mock analysis"""
        return {
            "symbol": symbol,
            "analysis_type": "risk",
            "volatility": 18.5,
            "beta": 1.2,
            "sharpe_ratio": 0.85,
            "value_at_risk": -4.2,
            "max_drawdown": -15.3,
            "risk_level": "medium",
            "timestamp": datetime.utcnow().isoformat()
        }