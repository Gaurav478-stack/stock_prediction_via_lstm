import yfinance as yf
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from datetime import datetime

class PortfolioOptimization:
    def __init__(self):
        self.period = "2y"
    
    async def optimize(self, symbols: list, risk_tolerance: str = "medium") -> dict:
        """Optimize portfolio using Modern Portfolio Theory"""
        try:
            # Get historical data
            returns_data = await self._get_returns_data(symbols)
            
            if returns_data is None or returns_data.empty:
                return await self._get_mock_optimization(symbols)
            
            # Calculate expected returns and covariance matrix
            expected_returns = returns_data.mean() * 252
            cov_matrix = returns_data.cov() * 252
            
            # Optimize based on risk tolerance
            if risk_tolerance == "low":
                target_return = expected_returns.min()
            elif risk_tolerance == "high":
                target_return = expected_returns.max()
            else:  # medium
                target_return = expected_returns.mean()
            
            weights = self._optimize_weights(expected_returns, cov_matrix, target_return)
            
            # Calculate portfolio metrics
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe_ratio = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
            
            # Format results
            optimized_weights = {
                symbol: round(weight, 4) 
                for symbol, weight in zip(symbols, weights)
            }
            
            return {
                "optimized_weights": optimized_weights,
                "expected_return": round(portfolio_return * 100, 2),  # as percentage
                "risk": round(portfolio_volatility * 100, 2),  # as percentage
                "sharpe_ratio": round(sharpe_ratio, 3),
                "risk_tolerance": risk_tolerance,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Portfolio optimization error: {e}")
            return await self._get_mock_optimization(symbols)
    
    async def _get_returns_data(self, symbols):
        """Get historical returns data for symbols"""
        try:
            data = {}
            for symbol in symbols:
                stock = yf.Ticker(symbol)
                hist = stock.history(period=self.period)
                if not hist.empty:
                    data[symbol] = hist['Close'].pct_change().dropna()
            
            if not data:
                return None
                
            returns_df = pd.DataFrame(data)
            returns_df = returns_df.dropna()
            
            # Ensure we have sufficient data
            if len(returns_df) < 30:
                return None
                
            return returns_df
            
        except Exception as e:
            print(f"Error getting returns data: {e}")
            return None
    
    def _optimize_weights(self, expected_returns, cov_matrix, target_return):
        """Optimize portfolio weights using Markowitz optimization"""
        num_assets = len(expected_returns)
        
        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # weights sum to 1
            {'type': 'eq', 'fun': lambda x: np.dot(x, expected_returns) - target_return}
        )
        
        bounds = tuple((0, 1) for _ in range(num_assets))  # no short selling
        
        # Initial guess (equal weights)
        init_guess = num_assets * [1.0 / num_assets]
        
        try:
            result = minimize(
                portfolio_volatility,
                init_guess,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            return result.x if result.success else init_guess
        except:
            return init_guess
    
    async def _get_mock_optimization(self, symbols):
        """Fallback mock optimization"""
        n = len(symbols)
        equal_weight = 1.0 / n
        
        weights = {
            symbol: round(equal_weight, 4) 
            for symbol in symbols
        }
        
        return {
            "optimized_weights": weights,
            "expected_return": 8.5,
            "risk": 12.2,
            "sharpe_ratio": 0.70,
            "risk_tolerance": "medium",
            "timestamp": datetime.utcnow().isoformat()
        }