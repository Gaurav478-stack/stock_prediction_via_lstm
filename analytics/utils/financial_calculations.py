import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Tuple
import math

class FinancialCalculations:
    """
    Advanced financial calculations and formulas
    """
    
    @staticmethod
    def calculate_portfolio_variance(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
        """
        Calculate portfolio variance using Markowitz formula
        """
        return np.dot(weights.T, np.dot(cov_matrix, weights))
    
    @staticmethod
    def calculate_portfolio_return(weights: np.ndarray, expected_returns: np.ndarray) -> float:
        """
        Calculate expected portfolio return
        """
        return np.dot(weights, expected_returns)
    
    @staticmethod
    def calculate_sharpe_ratio(portfolio_return: float, portfolio_volatility: float, 
                             risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio
        """
        if portfolio_volatility == 0:
            return 0
        return (portfolio_return - risk_free_rate) / portfolio_volatility
    
    @staticmethod
    def calculate_sortino_ratio(portfolio_return: float, downside_volatility: float,
                              risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sortino ratio (focuses on downside risk)
        """
        if downside_volatility == 0:
            return 0
        return (portfolio_return - risk_free_rate) / downside_volatility
    
    @staticmethod
    def calculate_treynor_ratio(portfolio_return: float, beta: float,
                              risk_free_rate: float = 0.02) -> float:
        """
        Calculate Treynor ratio (return per unit of systematic risk)
        """
        if beta == 0:
            return 0
        return (portfolio_return - risk_free_rate) / beta
    
    @staticmethod
    def calculate_jensens_alpha(portfolio_return: float, expected_return: float,
                              risk_free_rate: float = 0.02) -> float:
        """
        Calculate Jensen's Alpha (excess return over expected)
        """
        return portfolio_return - (risk_free_rate + expected_return)
    
    @staticmethod
    def calculate_value_at_risk(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """
        Calculate Value at Risk (VaR) using historical method
        """
        if returns.empty:
            return 0
        return np.percentile(returns, confidence_level * 100)
    
    @staticmethod
    def calculate_conditional_var(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall
        """
        if returns.empty:
            return 0
        var = FinancialCalculations.calculate_value_at_risk(returns, confidence_level)
        cvar = returns[returns <= var].mean()
        return cvar if not np.isnan(cvar) else var
    
    @staticmethod
    def calculate_max_drawdown(prices: pd.Series) -> float:
        """
        Calculate maximum drawdown
        """
        if prices.empty:
            return 0
        
        cumulative_returns = (1 + prices.pct_change().fillna(0)).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        
        return drawdown.min()
    
    @staticmethod
    def calculate_calmar_ratio(annual_return: float, max_drawdown: float) -> float:
        """
        Calculate Calmar ratio (return relative to max drawdown)
        """
        if max_drawdown == 0:
            return 0
        return annual_return / abs(max_drawdown)
    
    @staticmethod
    def calculate_information_ratio(portfolio_returns: pd.Series, 
                                  benchmark_returns: pd.Series) -> float:
        """
        Calculate Information ratio (excess return per unit of active risk)
        """
        active_returns = portfolio_returns - benchmark_returns
        if len(active_returns) < 2:
            return 0
        
        tracking_error = active_returns.std()
        if tracking_error == 0:
            return 0
        
        return active_returns.mean() / tracking_error
    
    @staticmethod
    def calculate_alpha_beta(portfolio_returns: pd.Series, 
                           benchmark_returns: pd.Series,
                           risk_free_rate: float = 0.02) -> Tuple[float, float]:
        """
        Calculate Alpha and Beta using CAPM
        """
        # Align returns
        aligned_returns = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
        if len(aligned_returns) < 2:
            return 0, 1
        
        portfolio_aligned = aligned_returns.iloc[:, 0]
        benchmark_aligned = aligned_returns.iloc[:, 1]
        
        # Calculate beta (covariance / variance)
        covariance = np.cov(portfolio_aligned, benchmark_aligned)[0, 1]
        variance = np.var(benchmark_aligned)
        beta = covariance / variance if variance != 0 else 1
        
        # Calculate alpha using CAPM
        alpha = portfolio_aligned.mean() - (risk_free_rate/252 + beta * (benchmark_aligned.mean() - risk_free_rate/252))
        
        return alpha * 252, beta  # Annualize alpha
    
    @staticmethod
    def calculate_black_scholes(S: float, K: float, T: float, r: float, 
                              sigma: float, option_type: str = 'call') -> float:
        """
        Calculate Black-Scholes option price
        """
        if T <= 0:
            if option_type == 'call':
                return max(S - K, 0)
            else:
                return max(K - S, 0)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == 'call':
            price = S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
        else:  # put
            price = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
        
        return price
    
    @staticmethod
    def calculate_dividend_yield(annual_dividend: float, current_price: float) -> float:
        """
        Calculate dividend yield
        """
        if current_price == 0:
            return 0
        return annual_dividend / current_price
    
    @staticmethod
    def calculate_earnings_yield(eps: float, current_price: float) -> float:
        """
        Calculate earnings yield (inverse of P/E ratio)
        """
        if current_price == 0:
            return 0
        return eps / current_price
    
    @staticmethod
    def calculate_compound_annual_growth_rate(beginning_value: float, 
                                            ending_value: float, 
                                            years: float) -> float:
        """
        Calculate Compound Annual Growth Rate (CAGR)
        """
        if beginning_value <= 0 or years <= 0:
            return 0
        return (ending_value / beginning_value) ** (1 / years) - 1
    
    @staticmethod
    def calculate_present_value(future_value: float, rate: float, periods: int) -> float:
        """
        Calculate present value
        """
        return future_value / (1 + rate) ** periods
    
    @staticmethod
    def calculate_future_value(present_value: float, rate: float, periods: int) -> float:
        """
        Calculate future value
        """
        return present_value * (1 + rate) ** periods
    
    @staticmethod
    def calculate_annuity_payment(present_value: float, rate: float, periods: int) -> float:
        """
        Calculate annuity payment
        """
        if rate == 0:
            return present_value / periods
        
        return present_value * rate / (1 - (1 + rate) ** -periods)
    
    @staticmethod
    def calculate_internal_rate_of_return(cash_flows: List[float]) -> float:
        """
        Calculate Internal Rate of Return (IRR)
        """
        try:
            return np.irr(cash_flows)
        except:
            return 0
    
    @staticmethod
    def calculate_modified_duration(price: float, yield_change: float, 
                                  price_change: float) -> float:
        """
        Calculate modified duration for bonds
        """
        if price == 0:
            return 0
        return (-price_change / price) / yield_change
    
    @staticmethod
    def calculate_convexity(price: float, yield_up: float, yield_down: float,
                          price_up: float, price_down: float) -> float:
        """
        Calculate convexity for bonds
        """
        if price == 0:
            return 0
        
        yield_change = yield_up - yield_down
        if yield_change == 0:
            return 0
        
        return (price_up + price_down - 2 * price) / (price * (yield_change ** 2))
    
    @staticmethod
    def calculate_risk_adjusted_return(return_series: pd.Series, 
                                     risk_free_rate: float = 0.02,
                                     method: str = 'sharpe') -> float:
        """
        Calculate various risk-adjusted return measures
        """
        if return_series.empty:
            return 0
        
        annual_return = return_series.mean() * 252
        annual_volatility = return_series.std() * np.sqrt(252)
        
        if method == 'sharpe':
            return FinancialCalculations.calculate_sharpe_ratio(
                annual_return, annual_volatility, risk_free_rate
            )
        elif method == 'sortino':
            downside_returns = return_series[return_series < 0]
            downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
            return FinancialCalculations.calculate_sortino_ratio(
                annual_return, downside_volatility, risk_free_rate
            )
        elif method == 'treynor':
            # For Treynor, we need beta - using 1 as default
            return FinancialCalculations.calculate_treynor_ratio(
                annual_return, 1.0, risk_free_rate
            )
        else:
            return 0
    
    @staticmethod
    def calculate_technical_oscillators(prices: pd.Series, 
                                      volume: Optional[pd.Series] = None) -> Dict:
        """
        Calculate various technical oscillators
        """
        if prices.empty:
            return {}
        
        results = {}
        
        # RSI
        results['rsi'] = FinancialCalculations._calculate_rsi(prices)
        
        # Stochastic Oscillator
        results['stochastic'] = FinancialCalculations._calculate_stochastic_oscillator(prices)
        
        # Williams %R
        results['williams_r'] = FinancialCalculations._calculate_williams_r(prices)
        
        # CCI (Commodity Channel Index)
        results['cci'] = FinancialCalculations._calculate_cci(prices)
        
        if volume is not None:
            # Money Flow Index
            results['mfi'] = FinancialCalculations._calculate_mfi(prices, volume)
        
        return results
    
    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not rsi.empty else 50
    
    @staticmethod
    def _calculate_stochastic_oscillator(prices: pd.Series, period: int = 14) -> float:
        """Calculate Stochastic Oscillator %K"""
        if len(prices) < period:
            return 50
        
        low_min = prices.rolling(window=period).min()
        high_max = prices.rolling(window=period).max()
        
        stoch = 100 * (prices - low_min) / (high_max - low_min)
        return stoch.iloc[-1] if not stoch.empty else 50
    
    @staticmethod
    def _calculate_williams_r(prices: pd.Series, period: int = 14) -> float:
        """Calculate Williams %R"""
        if len(prices) < period:
            return -50
        
        high_max = prices.rolling(window=period).max()
        low_min = prices.rolling(window=period).min()
        
        williams_r = -100 * (high_max - prices) / (high_max - low_min)
        return williams_r.iloc[-1] if not williams_r.empty else -50
    
    @staticmethod
    def _calculate_cci(prices: pd.Series, period: int = 20) -> float:
        """Calculate Commodity Channel Index"""
        if len(prices) < period:
            return 0
        
        typical_price = (prices + prices.rolling(window=period).max() + prices.rolling(window=period).min()) / 3
        sma = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        
        cci = (typical_price - sma) / (0.015 * mad)
        return cci.iloc[-1] if not cci.empty else 0
    
    @staticmethod
    def _calculate_mfi(prices: pd.Series, volume: pd.Series, period: int = 14) -> float:
        """Calculate Money Flow Index"""
        if len(prices) < period or len(volume) < period:
            return 50
        
        typical_price = (prices + prices.shift(1) + prices.rolling(window=period).max()) / 3
        money_flow = typical_price * volume
        
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
        
        positive_sum = positive_flow.rolling(window=period).sum()
        negative_sum = negative_flow.rolling(window=period).sum()
        
        mfi = 100 - (100 / (1 + positive_sum / negative_sum))
        return mfi.iloc[-1] if not mfi.empty else 50