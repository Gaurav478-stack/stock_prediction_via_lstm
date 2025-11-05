import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

class PortfolioService:
    def __init__(self):
        pass
    
    def analyze_portfolio(self, holdings: list) -> dict:
        """
        Analyze portfolio with holdings
        holdings: [{"symbol": "AAPL", "shares": 10, "purchasePrice": 150}]
        """
        try:
            total_value = 0
            total_cost = 0
            positions = []
            
            for holding in holdings:
                symbol = holding.get('symbol')
                shares = holding.get('shares', 0)
                purchase_price = holding.get('purchasePrice', 0)
                
                # Get current price
                ticker = yf.Ticker(symbol)
                current_price = ticker.info.get('currentPrice', ticker.info.get('regularMarketPrice', 0))
                
                if current_price == 0:
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                
                position_value = current_price * shares
                position_cost = purchase_price * shares
                gain_loss = position_value - position_cost
                gain_loss_percent = (gain_loss / position_cost * 100) if position_cost > 0 else 0
                
                positions.append({
                    'symbol': symbol,
                    'shares': shares,
                    'purchasePrice': round(purchase_price, 2),
                    'currentPrice': round(float(current_price), 2),
                    'positionValue': round(float(position_value), 2),
                    'positionCost': round(float(position_cost), 2),
                    'gainLoss': round(float(gain_loss), 2),
                    'gainLossPercent': round(float(gain_loss_percent), 2)
                })
                
                total_value += position_value
                total_cost += position_cost
            
            total_gain_loss = total_value - total_cost
            total_gain_loss_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
            
            # Calculate allocation percentages
            for position in positions:
                position['allocationPercent'] = round((position['positionValue'] / total_value * 100) if total_value > 0 else 0, 2)
            
            return {
                'totalValue': round(float(total_value), 2),
                'totalCost': round(float(total_cost), 2),
                'totalGainLoss': round(float(total_gain_loss), 2),
                'totalGainLossPercent': round(float(total_gain_loss_percent), 2),
                'positions': positions,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing portfolio: {e}")
            raise
    
    def get_portfolio_performance(self, holdings: list, period: str = '1mo') -> dict:
        """Get portfolio performance over time"""
        try:
            symbols = [h['symbol'] for h in holdings]
            shares_map = {h['symbol']: h['shares'] for h in holdings}
            
            # Get historical data for all symbols
            portfolio_values = {}
            dates = None
            
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                
                if not hist.empty:
                    if dates is None:
                        dates = hist.index.tolist()
                    
                    portfolio_values[symbol] = (hist['Close'] * shares_map[symbol]).tolist()
            
            # Calculate total portfolio value for each date
            if dates and portfolio_values:
                total_values = []
                for i in range(len(dates)):
                    day_total = sum(values[i] if i < len(values) else 0 for values in portfolio_values.values())
                    total_values.append(round(float(day_total), 2))
                
                return {
                    'dates': [date.strftime('%Y-%m-%d') for date in dates],
                    'values': total_values,
                    'period': period
                }
            
            return {'dates': [], 'values': [], 'period': period}
            
        except Exception as e:
            print(f"Error getting portfolio performance: {e}")
            return {'dates': [], 'values': [], 'period': period}
    
    def get_diversification_score(self, holdings: list) -> dict:
        """Calculate portfolio diversification score"""
        try:
            if not holdings:
                return {'score': 0, 'rating': 'N/A', 'message': 'No holdings'}
            
            # Simple diversification based on number of positions and allocation balance
            num_positions = len(holdings)
            
            # Get total value
            total_value = sum(h.get('shares', 0) * h.get('purchasePrice', 0) for h in holdings)
            
            # Calculate Herfindahl index (concentration measure)
            allocations = [(h.get('shares', 0) * h.get('purchasePrice', 0)) / total_value for h in holdings if total_value > 0]
            herfindahl_index = sum(a ** 2 for a in allocations)
            
            # Diversification score (0-100)
            # Perfect diversification would have HHI close to 0, concentrated portfolio close to 1
            diversification_score = (1 - herfindahl_index) * 100
            
            # Rating
            if diversification_score >= 80:
                rating = 'Excellent'
            elif diversification_score >= 60:
                rating = 'Good'
            elif diversification_score >= 40:
                rating = 'Fair'
            else:
                rating = 'Poor'
            
            return {
                'score': round(diversification_score, 1),
                'rating': rating,
                'numPositions': num_positions,
                'message': f'Portfolio has {num_positions} positions with {rating.lower()} diversification'
            }
            
        except Exception as e:
            print(f"Error calculating diversification: {e}")
            return {'score': 0, 'rating': 'Error', 'message': str(e)}
