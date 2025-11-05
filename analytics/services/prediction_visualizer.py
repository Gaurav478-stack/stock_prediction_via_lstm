"""
Stock Prediction Visualization Service
Generates beautiful charts for LSTM predictions using matplotlib and plotly
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io
import base64
from pathlib import Path

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 16


class PredictionVisualizer:
    """Generate visualizations for stock predictions"""
    
    def __init__(self, output_dir='visualizations'):
        """Initialize visualizer with output directory"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def create_prediction_chart(self, symbol, historical_dates, historical_prices,
                               prediction_dates, predictions, current_price,
                               predicted_price, save_path=None):
        """
        Create a comprehensive prediction chart
        
        Args:
            symbol: Stock symbol
            historical_dates: List of historical dates
            historical_prices: List of historical prices
            prediction_dates: List of prediction dates
            predictions: List of predicted prices
            current_price: Current stock price
            predicted_price: Final predicted price
            save_path: Path to save the image (optional)
            
        Returns:
            Path to saved image or base64 encoded image
        """
        fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
        
        # Convert dates to datetime
        hist_dates = pd.to_datetime(historical_dates)
        pred_dates = pd.to_datetime(prediction_dates)
        
        # Plot historical prices
        ax.plot(hist_dates, historical_prices, 
               color='#3B82F6', linewidth=2.5, label='Historical Prices',
               marker='o', markersize=3, markevery=5)
        
        # Plot predicted prices
        ax.plot(pred_dates, predictions,
               color='#A855F7', linewidth=2.5, label='Predicted Prices',
               linestyle='--', marker='s', markersize=4, markevery=3)
        
        # Add vertical line at prediction start
        ax.axvline(x=hist_dates[-1], color='#EF4444', 
                  linestyle=':', linewidth=2, alpha=0.7, label='Prediction Start')
        
        # Add confidence band (simple ±5% band)
        pred_upper = np.array(predictions) * 1.05
        pred_lower = np.array(predictions) * 0.95
        ax.fill_between(pred_dates, pred_lower, pred_upper,
                        color='#A855F7', alpha=0.15, label='Confidence Band (±5%)')
        
        # Annotate current price
        ax.annotate(f'Current: ${current_price:.2f}',
                   xy=(hist_dates[-1], current_price),
                   xytext=(10, 20), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.5', fc='#3B82F6', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0',
                                 color='#3B82F6'),
                   fontsize=11, color='white', weight='bold')
        
        # Annotate predicted price
        price_change = ((predicted_price - current_price) / current_price) * 100
        change_color = '#10B981' if price_change >= 0 else '#EF4444'
        change_sign = '+' if price_change >= 0 else ''
        
        ax.annotate(f'Predicted: ${predicted_price:.2f}\n({change_sign}{price_change:.2f}%)',
                   xy=(pred_dates[-1], predicted_price),
                   xytext=(-80, -30), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.5', fc=change_color, alpha=0.8),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0',
                                 color=change_color),
                   fontsize=11, color='white', weight='bold')
        
        # Formatting
        ax.set_xlabel('Date', fontsize=13, weight='bold')
        ax.set_ylabel('Price ($)', fontsize=13, weight='bold')
        ax.set_title(f'{symbol} Stock Price Prediction - 30 Day Forecast',
                    fontsize=16, weight='bold', pad=20)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.xticks(rotation=45, ha='right')
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y:.2f}'))
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_facecolor('#F8FAFC')
        
        # Legend
        ax.legend(loc='upper left', framealpha=0.9, shadow=True)
        
        # Add metadata text
        days_predicted = len(predictions)
        metadata_text = f'Forecast Period: {days_predicted} days | Model: LSTM Neural Network'
        fig.text(0.5, 0.02, metadata_text, ha='center', fontsize=10,
                style='italic', color='gray')
        
        plt.tight_layout()
        
        # Save or return base64
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close()
            return save_path
        else:
            # Return base64 encoded image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            return f'data:image/png;base64,{img_base64}'
    
    def create_comparison_chart(self, symbol, historical_prices, predictions,
                               model_metadata=None, save_path=None):
        """
        Create a detailed comparison chart with multiple subplots
        
        Returns:
            Path or base64 encoded image
        """
        fig = plt.figure(figsize=(16, 12), dpi=100)
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # Subplot 1: Main prediction chart (top, spanning 2 columns)
        ax1 = fig.add_subplot(gs[0, :])
        self._plot_main_prediction(ax1, historical_prices, predictions, symbol)
        
        # Subplot 2: Price distribution
        ax2 = fig.add_subplot(gs[1, 0])
        self._plot_price_distribution(ax2, historical_prices, predictions)
        
        # Subplot 3: Daily returns
        ax3 = fig.add_subplot(gs[1, 1])
        self._plot_daily_returns(ax3, historical_prices, predictions)
        
        # Subplot 4: Volatility
        ax4 = fig.add_subplot(gs[2, 0])
        self._plot_volatility(ax4, historical_prices, predictions)
        
        # Subplot 5: Model metrics
        ax5 = fig.add_subplot(gs[2, 1])
        self._plot_model_metrics(ax5, model_metadata)
        
        fig.suptitle(f'{symbol} - Comprehensive Prediction Analysis',
                    fontsize=18, weight='bold', y=0.995)
        
        # Save or return base64
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close()
            return save_path
        else:
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            return f'data:image/png;base64,{img_base64}'
    
    def _plot_main_prediction(self, ax, historical_prices, predictions, symbol):
        """Plot main prediction line chart"""
        days_hist = len(historical_prices)
        days_pred = len(predictions)
        
        x_hist = np.arange(days_hist)
        x_pred = np.arange(days_hist, days_hist + days_pred)
        
        ax.plot(x_hist, historical_prices, 'b-', linewidth=2, label='Historical')
        ax.plot(x_pred, predictions, 'r--', linewidth=2, label='Predicted')
        ax.axvline(x=days_hist-1, color='gray', linestyle=':', alpha=0.5)
        
        ax.set_xlabel('Days')
        ax.set_ylabel('Price ($)')
        ax.set_title('Price Prediction Timeline')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_price_distribution(self, ax, historical_prices, predictions):
        """Plot price distribution histogram"""
        ax.hist(historical_prices, bins=30, alpha=0.6, color='blue',
               label='Historical', density=True)
        ax.hist(predictions, bins=20, alpha=0.6, color='red',
               label='Predicted', density=True)
        ax.set_xlabel('Price ($)')
        ax.set_ylabel('Density')
        ax.set_title('Price Distribution')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_daily_returns(self, ax, historical_prices, predictions):
        """Plot daily returns"""
        hist_returns = np.diff(historical_prices) / historical_prices[:-1] * 100
        pred_returns = np.diff(predictions) / predictions[:-1] * 100
        
        ax.plot(hist_returns, 'b-', alpha=0.7, linewidth=1, label='Historical Returns')
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
        ax.axhline(y=np.mean(pred_returns), color='red', linestyle='--',
                  alpha=0.7, label=f'Avg Predicted: {np.mean(pred_returns):.2f}%')
        
        ax.set_xlabel('Days')
        ax.set_ylabel('Daily Return (%)')
        ax.set_title('Daily Returns Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_volatility(self, ax, historical_prices, predictions):
        """Plot rolling volatility"""
        window = min(20, len(historical_prices) // 2)
        hist_returns = np.diff(historical_prices) / historical_prices[:-1]
        rolling_vol = pd.Series(hist_returns).rolling(window=window).std() * 100
        
        ax.plot(rolling_vol, 'b-', linewidth=2, label=f'{window}-Day Rolling Volatility')
        ax.axhline(y=np.nanmean(rolling_vol), color='red', linestyle='--',
                  alpha=0.7, label=f'Mean: {np.nanmean(rolling_vol):.2f}%')
        
        ax.set_xlabel('Days')
        ax.set_ylabel('Volatility (%)')
        ax.set_title('Historical Volatility')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_model_metrics(self, ax, model_metadata):
        """Plot model performance metrics"""
        if not model_metadata:
            ax.text(0.5, 0.5, 'No Model Metadata Available',
                   ha='center', va='center', fontsize=12)
            ax.axis('off')
            return
        
        metrics = {
            'Test MAE': model_metadata.get('test_mae', 0) * 100,
            'Test Loss': model_metadata.get('test_loss', 0) * 100,
            'Train Loss': model_metadata.get('final_train_loss', 0) * 100,
            'Accuracy': max(0, 100 - model_metadata.get('test_mae', 0) * 100)
        }
        
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#A855F7']
        bars = ax.barh(list(metrics.keys()), list(metrics.values()), color=colors)
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f'{width:.2f}%',
                   ha='left', va='center', fontsize=10, weight='bold')
        
        ax.set_xlabel('Score (%)')
        ax.set_title('Model Performance Metrics')
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_xlim(0, 100)


def generate_prediction_visualization(prediction_data, output_format='base64'):
    """
    Generate visualization from prediction data
    
    Args:
        prediction_data: Dict with prediction results from lstm_prediction
        output_format: 'base64' or 'file'
        
    Returns:
        base64 string or file path
    """
    visualizer = PredictionVisualizer()
    
    symbol = prediction_data.get('symbol', 'UNKNOWN')
    
    # Convert date strings to datetime objects
    historical_dates_str = prediction_data.get('historical_dates', [])
    future_dates_str = prediction_data.get('future_dates', [])
    
    historical_dates = pd.to_datetime(historical_dates_str)
    future_dates = pd.to_datetime(future_dates_str)
    
    historical_prices = prediction_data.get('historical_prices', [])
    predictions = prediction_data.get('predictions', [])
    current_price = prediction_data.get('current_price', 0)
    predicted_price = prediction_data.get('predicted_price', 0)
    
    if output_format == 'file':
        save_path = visualizer.output_dir / f'{symbol}_prediction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        return visualizer.create_prediction_chart(
            symbol, historical_dates, historical_prices,
            future_dates, predictions, current_price,
            predicted_price, save_path=save_path
        )
    else:
        return visualizer.create_prediction_chart(
            symbol, historical_dates, historical_prices,
            future_dates, predictions, current_price,
            predicted_price
        )


def generate_comprehensive_analysis(prediction_data, output_format='base64'):
    """
    Generate comprehensive analysis with multiple charts
    """
    visualizer = PredictionVisualizer()
    
    symbol = prediction_data.get('symbol', 'UNKNOWN')
    historical_prices = prediction_data.get('historical_prices', [])
    predictions = prediction_data.get('predictions', [])
    model_metadata = prediction_data.get('model_metadata', {})
    
    if output_format == 'file':
        save_path = visualizer.output_dir / f'{symbol}_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        return visualizer.create_comparison_chart(
            symbol, historical_prices, predictions,
            model_metadata, save_path=save_path
        )
    else:
        return visualizer.create_comparison_chart(
            symbol, historical_prices, predictions,
            model_metadata
        )


# Test function
if __name__ == '__main__':
    print("=== Stock Prediction Visualizer Test ===\n")
    
    # Create sample data
    historical_dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
    historical_prices = 100 + np.cumsum(np.random.randn(60)) * 2
    
    prediction_dates = pd.date_range(start=historical_dates[-1] + timedelta(days=1),
                                     periods=30, freq='D')
    predictions = historical_prices[-1] + np.cumsum(np.random.randn(30)) * 1.5
    
    test_data = {
        'symbol': 'TEST',
        'historical_dates': historical_dates.strftime('%Y-%m-%d').tolist(),
        'historical_prices': historical_prices.tolist(),
        'future_dates': prediction_dates.strftime('%Y-%m-%d').tolist(),
        'predictions': predictions.tolist(),
        'current_price': historical_prices[-1],
        'predicted_price': predictions[-1],
        'model_metadata': {
            'test_mae': 0.10,
            'test_loss': 0.02,
            'final_train_loss': 0.01
        }
    }
    
    # Generate visualizations
    print("Generating prediction chart...")
    img1 = generate_prediction_visualization(test_data, output_format='file')
    print(f"✅ Saved to: {img1}")
    
    print("\nGenerating comprehensive analysis...")
    img2 = generate_comprehensive_analysis(test_data, output_format='file')
    print(f"✅ Saved to: {img2}")
    
    print("\n✅ Test complete!")
