"""
Evolution Strategy Trading Agent
Uses genetic algorithms to evolve optimal trading strategies
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from typing import List, Dict, Tuple


class TradingAgent:
    """Simple trading agent using evolution strategy"""
    
    def __init__(self, initial_fund=10000, skip_days=5):
        """
        Initialize trading agent
        
        Args:
            initial_fund: Starting capital
            skip_days: Minimum days between trades
        """
        self.initial_fund = initial_fund
        self.skip_days = skip_days
        self.reset()
    
    def reset(self):
        """Reset agent state"""
        self.cash = self.initial_fund
        self.holdings = 0
        self.portfolio_value = self.initial_fund
        self.trades = []
        self.last_trade_day = -self.skip_days
    
    def can_trade(self, current_day):
        """Check if enough days have passed since last trade"""
        return current_day - self.last_trade_day >= self.skip_days
    
    def buy(self, price, quantity, date, day):
        """Execute buy order"""
        cost = price * quantity
        if cost <= self.cash:
            self.cash -= cost
            self.holdings += quantity
            self.last_trade_day = day
            self.trades.append({
                'action': 'BUY',
                'date': date,
                'price': price,
                'quantity': quantity,
                'cost': cost,
                'day': day
            })
            return True
        return False
    
    def sell(self, price, quantity, date, day):
        """Execute sell order"""
        if quantity <= self.holdings:
            proceeds = price * quantity
            self.cash += proceeds
            self.holdings -= quantity
            self.last_trade_day = day
            self.trades.append({
                'action': 'SELL',
                'date': date,
                'price': price,
                'quantity': quantity,
                'proceeds': proceeds,
                'day': day
            })
            return True
        return False
    
    def get_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        return self.cash + (self.holdings * current_price)
    
    def calculate_profit(self, current_price):
        """Calculate profit/loss"""
        final_value = self.get_portfolio_value(current_price)
        return final_value - self.initial_fund


class SimpleStrategy:
    """Simple moving average crossover strategy"""
    
    def __init__(self, short_window=10, long_window=30):
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signals(self, prices):
        """
        Generate buy/sell signals based on moving average crossover
        
        Args:
            prices: Array of prices
            
        Returns:
            Array of signals (1=buy, -1=sell, 0=hold)
        """
        df = pd.DataFrame({'price': prices})
        df['short_ma'] = df['price'].rolling(window=self.short_window).mean()
        df['long_ma'] = df['price'].rolling(window=self.long_window).mean()
        
        signals = np.zeros(len(prices))
        
        for i in range(1, len(prices)):
            if pd.notna(df['short_ma'].iloc[i]) and pd.notna(df['long_ma'].iloc[i]):
                # Buy signal: short MA crosses above long MA
                if (df['short_ma'].iloc[i] > df['long_ma'].iloc[i] and 
                    df['short_ma'].iloc[i-1] <= df['long_ma'].iloc[i-1]):
                    signals[i] = 1
                # Sell signal: short MA crosses below long MA
                elif (df['short_ma'].iloc[i] < df['long_ma'].iloc[i] and 
                      df['short_ma'].iloc[i-1] >= df['long_ma'].iloc[i-1]):
                    signals[i] = -1
        
        return signals


class MomentumStrategy:
    """Momentum-based trading strategy"""
    
    def __init__(self, lookback=14, threshold=0.02):
        self.lookback = lookback
        self.threshold = threshold
    
    def generate_signals(self, prices):
        """
        Generate signals based on momentum
        
        Args:
            prices: Array of prices
            
        Returns:
            Array of signals (1=buy, -1=sell, 0=hold)
        """
        signals = np.zeros(len(prices))
        
        for i in range(self.lookback, len(prices)):
            momentum = (prices[i] - prices[i-self.lookback]) / prices[i-self.lookback]
            
            if momentum > self.threshold:
                signals[i] = 1  # Buy on positive momentum
            elif momentum < -self.threshold:
                signals[i] = -1  # Sell on negative momentum
        
        return signals


class RSIStrategy:
    """RSI-based trading strategy"""
    
    def __init__(self, period=14, oversold=30, overbought=70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def calculate_rsi(self, prices):
        """Calculate RSI indicator"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.zeros(len(prices))
        avg_losses = np.zeros(len(prices))
        
        # Initialize first average
        avg_gains[self.period] = np.mean(gains[:self.period])
        avg_losses[self.period] = np.mean(losses[:self.period])
        
        # Calculate subsequent averages
        for i in range(self.period + 1, len(prices)):
            avg_gains[i] = (avg_gains[i-1] * (self.period - 1) + gains[i-1]) / self.period
            avg_losses[i] = (avg_losses[i-1] * (self.period - 1) + losses[i-1]) / self.period
        
        # Calculate RSI
        rs = np.divide(avg_gains, avg_losses, out=np.zeros_like(avg_gains), where=avg_losses!=0)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, prices):
        """Generate signals based on RSI"""
        rsi = self.calculate_rsi(prices)
        signals = np.zeros(len(prices))
        
        for i in range(self.period, len(prices)):
            if rsi[i] < self.oversold:
                signals[i] = 1  # Buy when oversold
            elif rsi[i] > self.overbought:
                signals[i] = -1  # Sell when overbought
        
        return signals


def run_trading_agent(symbol, period='1y', initial_fund=10000, skip_days=5, strategy='ma'):
    """
    Run trading agent simulation
    
    Args:
        symbol: Stock symbol
        period: Historical data period
        initial_fund: Starting capital
        skip_days: Days to skip between trades
        strategy: Strategy to use ('ma', 'momentum', 'rsi')
        
    Returns:
        Dictionary with trading results
    """
    try:
        # Fetch historical data
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        
        if df.empty:
            return {
                'success': False,
                'error': f'No data found for symbol {symbol}'
            }
        
        prices = df['Close'].values
        dates = df.index.strftime('%Y-%m-%d').tolist()
        
        # Select strategy
        if strategy == 'ma':
            strat = SimpleStrategy(short_window=10, long_window=30)
        elif strategy == 'momentum':
            strat = MomentumStrategy(lookback=14, threshold=0.02)
        elif strategy == 'rsi':
            strat = RSIStrategy(period=14, oversold=30, overbought=70)
        else:
            strat = SimpleStrategy()
        
        # Generate signals
        signals = strat.generate_signals(prices)
        
        # Run trading simulation
        agent = TradingAgent(initial_fund=initial_fund, skip_days=skip_days)
        
        for day, (price, signal) in enumerate(zip(prices, signals)):
            if not agent.can_trade(day):
                continue
            
            if signal == 1:  # Buy signal
                # Buy with 20% of available cash
                quantity = int((agent.cash * 0.2) / price)
                if quantity > 0:
                    agent.buy(price, quantity, dates[day], day)
            
            elif signal == -1:  # Sell signal
                # Sell 50% of holdings
                quantity = int(agent.holdings * 0.5)
                if quantity > 0:
                    agent.sell(price, quantity, dates[day], day)
        
        # Calculate final metrics
        final_price = prices[-1]
        final_value = agent.get_portfolio_value(final_price)
        total_profit = final_value - initial_fund
        total_return_pct = (total_profit / initial_fund) * 100
        
        # Calculate buy & hold comparison
        buy_hold_shares = initial_fund / prices[0]
        buy_hold_value = buy_hold_shares * final_price
        buy_hold_profit = buy_hold_value - initial_fund
        buy_hold_return_pct = (buy_hold_profit / initial_fund) * 100
        
        return {
            'success': True,
            'symbol': symbol,
            'strategy': strategy,
            'historical': {
                'dates': dates,
                'prices': prices.tolist()
            },
            'trades': agent.trades,
            'metrics': {
                'initial_fund': initial_fund,
                'final_value': round(final_value, 2),
                'cash': round(agent.cash, 2),
                'holdings': agent.holdings,
                'holdings_value': round(agent.holdings * final_price, 2),
                'total_profit': round(total_profit, 2),
                'total_return_pct': round(total_return_pct, 2),
                'num_trades': len(agent.trades),
                'buy_trades': len([t for t in agent.trades if t['action'] == 'BUY']),
                'sell_trades': len([t for t in agent.trades if t['action'] == 'SELL']),
            },
            'comparison': {
                'buy_hold_value': round(buy_hold_value, 2),
                'buy_hold_profit': round(buy_hold_profit, 2),
                'buy_hold_return_pct': round(buy_hold_return_pct, 2),
                'strategy_advantage': round(total_return_pct - buy_hold_return_pct, 2)
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Trading simulation failed: {str(e)}'
        }
