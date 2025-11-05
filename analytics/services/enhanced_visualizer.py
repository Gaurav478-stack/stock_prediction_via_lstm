"""
Enhanced Stock Prediction Visualization Service
Generates advanced, interactive-style charts using matplotlib and seaborn
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from datetime import datetime, timedelta
import seaborn as sns
import io
import base64
from pathlib import Path

# Enhanced styling
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class EnhancedVisualizer:
    """Advanced visualization generator for stock predictions"""
    
    def __init__(self, output_dir='visualizations'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Color scheme
        self.colors = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6',
            'purple': '#a855f7',
            'cyan': '#06b6d4',
            'dark': '#1e293b',
            'light': '#f1f5f9'
        }
    
    def create_advanced_dashboard(self, prediction_data):
        """
        Create an advanced dashboard with multiple visualizations
        
        Args:
            prediction_data: Dict containing prediction results
            
        Returns:
            Base64 encoded PNG image
        """
        # Extract data
        symbol = prediction_data.get('symbol', 'UNKNOWN')
        hist_dates = pd.to_datetime(prediction_data.get('historical_dates', []))
        hist_prices = np.array(prediction_data.get('historical_prices', []))
        pred_dates = pd.to_datetime(prediction_data.get('future_dates', []))
        predictions = np.array(prediction_data.get('predictions', []))
        current_price = prediction_data.get('current_price', 0)
        predicted_price = prediction_data.get('predicted_price', 0)
        
        # Create figure with advanced layout (adjusted for better screen fit)
        fig = plt.figure(figsize=(16, 9))
        gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.35, 
                     top=0.95, bottom=0.06, left=0.06, right=0.96)
        
        # Main chart (top, spanning 2 columns)
        ax_main = fig.add_subplot(gs[0, :2])
        self._plot_main_prediction(ax_main, symbol, hist_dates, hist_prices, 
                                   pred_dates, predictions, current_price, predicted_price)
        
        # Candlestick-style view (top right)
        ax_candle = fig.add_subplot(gs[0, 2])
        self._plot_price_momentum(ax_candle, hist_prices, predictions)
        
        # Volume-like indicator (middle left)
        ax_volume = fig.add_subplot(gs[1, 0])
        self._plot_volatility_gauge(ax_volume, hist_prices)
        
        # Technical indicators (middle center)
        ax_tech = fig.add_subplot(gs[1, 1])
        self._plot_technical_summary(ax_tech, hist_prices, predictions)
        
        # Confidence meter (middle right)
        ax_confidence = fig.add_subplot(gs[1, 2])
        self._plot_confidence_meter(ax_confidence, prediction_data.get('model_metadata', {}))
        
        # Statistical distribution (bottom left)
        ax_dist = fig.add_subplot(gs[2, 0])
        self._plot_returns_distribution(ax_dist, hist_prices)
        
        # Prediction accuracy (bottom center)
        ax_accuracy = fig.add_subplot(gs[2, 1])
        self._plot_accuracy_metrics(ax_accuracy, prediction_data.get('model_metadata', {}))
        
        # Risk indicator (bottom right)
        ax_risk = fig.add_subplot(gs[2, 2])
        self._plot_risk_gauge(ax_risk, hist_prices, predictions)
        
        # Overall title
        change_pct = ((predicted_price - current_price) / current_price) * 100
        direction = "↑" if change_pct >= 0 else "↓"
        color = self.colors['success'] if change_pct >= 0 else self.colors['danger']
        
        fig.suptitle(f'{symbol} AI Analysis Dashboard - {direction} {abs(change_pct):.2f}% Predicted',
                    fontsize=20, fontweight='bold', color=color)
        
        # Save or encode
        return self._save_or_encode(fig)
    
    def _plot_main_prediction(self, ax, symbol, hist_dates, hist_prices, 
                             pred_dates, predictions, current_price, predicted_price):
        """Enhanced main prediction chart with gradient fills"""
        # Historical data with gradient
        ax.plot(hist_dates, hist_prices, color=self.colors['info'], 
               linewidth=2.5, label='Historical', alpha=0.9)
        ax.fill_between(hist_dates, hist_prices, alpha=0.3, color=self.colors['info'])
        
        # Predictions with gradient
        ax.plot(pred_dates, predictions, color=self.colors['purple'], 
               linewidth=2.5, linestyle='--', label='Prediction', alpha=0.9, marker='o', 
               markersize=4, markevery=5)
        ax.fill_between(pred_dates, predictions, alpha=0.2, color=self.colors['purple'])
        
        # Confidence bands
        upper_band = predictions * 1.05
        lower_band = predictions * 0.95
        ax.fill_between(pred_dates, lower_band, upper_band, 
                       alpha=0.15, color=self.colors['warning'], label='Confidence (±5%)')
        
        # Prediction start line
        ax.axvline(x=hist_dates[-1], color=self.colors['danger'], 
                  linestyle=':', linewidth=2, alpha=0.7, label='Prediction Start')
        
        # Annotations
        change_pct = ((predicted_price - current_price) / current_price) * 100
        change_color = self.colors['success'] if change_pct >= 0 else self.colors['danger']
        
        # Current price annotation
        ax.annotate(f'Current\n${current_price:.2f}',
                   xy=(hist_dates[-1], current_price),
                   xytext=(15, 25), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.6', fc=self.colors['info'], 
                           alpha=0.8, edgecolor='white', linewidth=2),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2',
                                 color='white', lw=2),
                   fontsize=11, color='white', weight='bold', ha='left')
        
        # Predicted price annotation
        ax.annotate(f'Predicted\n${predicted_price:.2f}\n({change_pct:+.2f}%)',
                   xy=(pred_dates[-1], predicted_price),
                   xytext=(-80, -40), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.6', fc=change_color, 
                           alpha=0.9, edgecolor='white', linewidth=2),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=-.2',
                                 color='white', lw=2),
                   fontsize=11, color='white', weight='bold', ha='right')
        
        # Styling
        ax.set_xlabel('Date', fontsize=12, weight='bold')
        ax.set_ylabel('Price ($)', fontsize=12, weight='bold')
        ax.set_title(f'{symbol} Price Forecast - 30 Day Prediction', 
                    fontsize=14, weight='bold', pad=15)
        ax.legend(loc='upper left', framealpha=0.9, fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.tick_params(axis='both', which='major', labelsize=9)
        
        # Background gradient
        ax.set_facecolor('#f8fafc')
    
    def _plot_price_momentum(self, ax, hist_prices, predictions):
        """Plot price momentum indicator"""
        # Calculate momentum
        recent_prices = hist_prices[-30:]
        momentum = np.diff(recent_prices)
        
        colors = [self.colors['success'] if m > 0 else self.colors['danger'] for m in momentum]
        
        ax.bar(range(len(momentum)), momentum, color=colors, alpha=0.7, edgecolor='white', linewidth=0.5)
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
        
        # Prediction momentum
        pred_momentum = np.mean(np.diff(predictions))
        ax.axhline(y=pred_momentum, color=self.colors['purple'], 
                  linestyle='--', linewidth=2, label=f'Pred. Momentum: ${pred_momentum:.2f}')
        
        ax.set_title('Price Momentum (Last 30 Days)', fontsize=11, weight='bold')
        ax.set_xlabel('Days', fontsize=9)
        ax.set_ylabel('Price Change ($)', fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)
        ax.set_facecolor('#f8fafc')
    
    def _plot_volatility_gauge(self, ax, hist_prices):
        """Plot volatility as a gauge"""
        # Calculate volatility metrics
        returns = np.diff(hist_prices) / hist_prices[:-1]
        volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized
        
        # Create gauge
        theta = np.linspace(0, np.pi, 100)
        r = 1
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        # Background arc
        ax.plot(x, y, color='lightgray', linewidth=15, alpha=0.3)
        
        # Colored sections
        sections = [
            (0, np.pi/3, self.colors['success'], 'Low'),
            (np.pi/3, 2*np.pi/3, self.colors['warning'], 'Medium'),
            (2*np.pi/3, np.pi, self.colors['danger'], 'High')
        ]
        
        for start, end, color, label in sections:
            theta_section = np.linspace(start, end, 30)
            x_section = r * np.cos(theta_section)
            y_section = r * np.sin(theta_section)
            ax.plot(x_section, y_section, color=color, linewidth=15, alpha=0.6)
        
        # Needle
        volatility_norm = min(volatility / 50, 1)  # Normalize to 0-1
        needle_angle = np.pi * (1 - volatility_norm)
        ax.plot([0, 0.9 * np.cos(needle_angle)], [0, 0.9 * np.sin(needle_angle)],
               color='black', linewidth=3, marker='o', markersize=8)
        
        # Text
        ax.text(0, -0.3, f'{volatility:.1f}%', ha='center', va='center',
               fontsize=16, weight='bold', color=self.colors['dark'])
        ax.text(0, -0.5, 'Volatility', ha='center', va='center',
               fontsize=10, color='gray')
        
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.7, 1.2)
        ax.axis('off')
        ax.set_title('Volatility Gauge', fontsize=11, weight='bold', pad=10)
    
    def _plot_technical_summary(self, ax, hist_prices, predictions):
        """Plot technical indicators summary"""
        # Calculate indicators
        sma_20 = np.convolve(hist_prices, np.ones(20)/20, mode='valid')
        sma_50 = np.convolve(hist_prices, np.ones(50)/50, mode='valid')
        
        current = hist_prices[-1]
        indicators = {
            'Price vs SMA20': ((current - sma_20[-1]) / sma_20[-1] * 100),
            'Price vs SMA50': ((current - sma_50[-1]) / sma_50[-1] * 100),
            'Trend': ((hist_prices[-1] - hist_prices[-30]) / hist_prices[-30] * 100),
            'Prediction': ((predictions[-1] - current) / current * 100)
        }
        
        y_pos = np.arange(len(indicators))
        values = list(indicators.values())
        colors = [self.colors['success'] if v > 0 else self.colors['danger'] for v in values]
        
        bars = ax.barh(y_pos, values, color=colors, alpha=0.7, edgecolor='white', linewidth=1.5)
        
        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, values)):
            ax.text(val + (2 if val > 0 else -2), i, f'{val:+.1f}%',
                   ha='left' if val > 0 else 'right', va='center',
                   fontsize=9, weight='bold', color=colors[i])
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(indicators.keys(), fontsize=9)
        ax.axvline(x=0, color='gray', linestyle='-', linewidth=1.5, alpha=0.5)
        ax.set_xlabel('Change (%)', fontsize=9)
        ax.set_title('Technical Summary', fontsize=11, weight='bold')
        ax.grid(True, alpha=0.2, axis='x')
        ax.set_facecolor('#f8fafc')
    
    def _plot_confidence_meter(self, ax, metadata):
        """Plot model confidence as a circular meter"""
        # Extract confidence metrics
        r2 = metadata.get('r2_score', 0.9)
        confidence = r2 * 100
        
        # Create donut chart
        sizes = [confidence, 100 - confidence]
        colors = [self.colors['success'], '#e5e7eb']
        explode = (0.05, 0)
        
        wedges, texts = ax.pie(sizes, explode=explode, colors=colors,
                               startangle=90, counterclock=False,
                               wedgeprops=dict(width=0.4, edgecolor='white', linewidth=3))
        
        # Center text
        ax.text(0, 0, f'{confidence:.1f}%', ha='center', va='center',
               fontsize=24, weight='bold', color=self.colors['success'])
        ax.text(0, -0.25, 'Confidence', ha='center', va='center',
               fontsize=10, color='gray')
        
        # Metrics text
        mae = metadata.get('mae', 0)
        mape = metadata.get('mape', 0)
        ax.text(0, -0.95, f'MAE: ${mae:.2f} | MAPE: {mape:.2f}%',
               ha='center', va='center', fontsize=8, color='gray',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8))
        
        ax.set_title('Model Confidence', fontsize=11, weight='bold', pad=15)
    
    def _plot_returns_distribution(self, ax, hist_prices):
        """Plot returns distribution with KDE"""
        returns = np.diff(hist_prices) / hist_prices[:-1] * 100
        
        # Histogram
        n, bins, patches = ax.hist(returns, bins=30, alpha=0.6, color=self.colors['info'],
                                   edgecolor='white', linewidth=1)
        
        # Color bars based on value
        for i, patch in enumerate(patches):
            if bins[i] < 0:
                patch.set_facecolor(self.colors['danger'])
            else:
                patch.set_facecolor(self.colors['success'])
        
        # KDE overlay
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(returns)
        x_range = np.linspace(returns.min(), returns.max(), 100)
        kde_values = kde(x_range) * len(returns) * (bins[1] - bins[0])
        ax.plot(x_range, kde_values, color=self.colors['dark'], linewidth=2, label='KDE')
        
        # Mean line
        ax.axvline(x=np.mean(returns), color=self.colors['warning'], 
                  linestyle='--', linewidth=2, label=f'Mean: {np.mean(returns):.2f}%')
        
        ax.set_xlabel('Daily Returns (%)', fontsize=9)
        ax.set_ylabel('Frequency', fontsize=9)
        ax.set_title('Returns Distribution', fontsize=11, weight='bold')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2, axis='y')
        ax.set_facecolor('#f8fafc')
    
    def _plot_accuracy_metrics(self, ax, metadata):
        """Plot accuracy metrics as horizontal bars"""
        metrics = {
            'R² Score': metadata.get('r2_score', 0) * 100,
            'Accuracy': (1 - metadata.get('mape', 5)/100) * 100,
            'Precision': 100 - metadata.get('mae', 2.5),
            'Reliability': metadata.get('test_loss', 0.02) * 1000 if metadata.get('test_loss', 0) < 0.1 else 85
        }
        
        y_pos = np.arange(len(metrics))
        values = list(metrics.values())
        
        # Create gradient bars
        bars = ax.barh(y_pos, values, color=self.colors['primary'], 
                      alpha=0.7, edgecolor='white', linewidth=1.5)
        
        # Color gradient based on value
        for bar, val in zip(bars, values):
            if val >= 90:
                bar.set_color(self.colors['success'])
            elif val >= 75:
                bar.set_color(self.colors['info'])
            else:
                bar.set_color(self.colors['warning'])
        
        # Add value labels
        for i, val in enumerate(values):
            ax.text(val + 2, i, f'{val:.1f}%', va='center',
                   fontsize=9, weight='bold')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(metrics.keys(), fontsize=9)
        ax.set_xlim(0, 105)
        ax.set_xlabel('Score (%)', fontsize=9)
        ax.set_title('Model Performance', fontsize=11, weight='bold')
        ax.grid(True, alpha=0.2, axis='x')
        ax.set_facecolor('#f8fafc')
    
    def _plot_risk_gauge(self, ax, hist_prices, predictions):
        """Plot risk assessment gauge"""
        # Calculate risk metrics
        hist_volatility = np.std(np.diff(hist_prices) / hist_prices[:-1]) * 100
        pred_volatility = np.std(np.diff(predictions) / predictions[:-1]) * 100
        
        # Determine risk level
        avg_volatility = (hist_volatility + pred_volatility) / 2
        if avg_volatility < 1.5:
            risk_level = "LOW"
            risk_color = self.colors['success']
            risk_score = 30
        elif avg_volatility < 3:
            risk_level = "MEDIUM"
            risk_color = self.colors['warning']
            risk_score = 60
        else:
            risk_level = "HIGH"
            risk_color = self.colors['danger']
            risk_score = 90
        
        # Create risk meter
        theta = np.linspace(0, np.pi, 100)
        r = 1
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        # Background
        ax.plot(x, y, color='lightgray', linewidth=12, alpha=0.3)
        
        # Risk arc
        risk_theta = np.linspace(0, np.pi * risk_score/100, 50)
        x_risk = r * np.cos(risk_theta)
        y_risk = r * np.sin(risk_theta)
        ax.plot(x_risk, y_risk, color=risk_color, linewidth=12, alpha=0.8)
        
        # Center text
        ax.text(0, 0.1, risk_level, ha='center', va='center',
               fontsize=18, weight='bold', color=risk_color)
        ax.text(0, -0.2, f'{avg_volatility:.2f}% Vol', ha='center', va='center',
               fontsize=10, color='gray')
        
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.5, 1.2)
        ax.axis('off')
        ax.set_title('Risk Assessment', fontsize=11, weight='bold', pad=10)
    
    def _save_or_encode(self, fig, save_path=None):
        """Save figure or return as base64"""
        if save_path:
            fig.savefig(save_path, dpi=100, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            return str(save_path)
        else:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            plt.close(fig)
            return img_base64


# Helper function for API
def generate_enhanced_dashboard(prediction_data, output_format='base64'):
    """Generate enhanced dashboard visualization"""
    viz = EnhancedVisualizer()
    return viz.create_advanced_dashboard(prediction_data)


if __name__ == '__main__':
    print("Enhanced Visualizer Ready!")
    print("Run from API to generate dashboards")
