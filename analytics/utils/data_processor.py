import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class DataProcessor:
    """
    Utility class for processing and cleaning financial data
    """
    
    @staticmethod
    def clean_stock_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess stock price data
        """
        if df.empty:
            return df
        
        # Make a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Ensure datetime index
        if not isinstance(cleaned_df.index, pd.DatetimeIndex):
            if 'Date' in cleaned_df.columns:
                cleaned_df['Date'] = pd.to_datetime(cleaned_df['Date'])
                cleaned_df.set_index('Date', inplace=True)
            else:
                # Try to infer datetime from index
                try:
                    cleaned_df.index = pd.to_datetime(cleaned_df.index)
                except:
                    # Create a dummy datetime index
                    cleaned_df.index = pd.date_range(
                        start='2020-01-01', 
                        periods=len(cleaned_df), 
                        freq='D'
                    )
        
        # Sort by date
        cleaned_df.sort_index(inplace=True)
        
        # Handle missing values
        cleaned_df = DataProcessor._handle_missing_values(cleaned_df)
        
        # Remove outliers using IQR method
        cleaned_df = DataProcessor._remove_outliers(cleaned_df)
        
        return cleaned_df
    
    @staticmethod
    def _handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in financial data
        """
        # Forward fill for small gaps, then backward fill
        df_ffilled = df.ffill()
        df_filled = df_ffilled.bfill()
        
        # If still missing values, use interpolation
        if df_filled.isnull().any().any():
            df_filled = df_filled.interpolate(method='linear')
        
        return df_filled
    
    @staticmethod
    def _remove_outliers(df: pd.DataFrame, method: str = 'iqr') -> pd.DataFrame:
        """
        Remove outliers from financial data using specified method
        """
        if method == 'iqr':
            return DataProcessor._remove_outliers_iqr(df)
        elif method == 'zscore':
            return DataProcessor._remove_outliers_zscore(df)
        else:
            return df
    
    @staticmethod
    def _remove_outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove outliers using Interquartile Range method
        """
        cleaned_df = df.copy()
        
        for column in cleaned_df.select_dtypes(include=[np.number]).columns:
            Q1 = cleaned_df[column].quantile(0.25)
            Q3 = cleaned_df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Cap outliers instead of removing (for time series)
            cleaned_df[column] = np.where(cleaned_df[column] < lower_bound, lower_bound, cleaned_df[column])
            cleaned_df[column] = np.where(cleaned_df[column] > upper_bound, upper_bound, cleaned_df[column])
        
        return cleaned_df
    
    @staticmethod
    def _remove_outliers_zscore(df: pd.DataFrame, threshold: float = 3) -> pd.DataFrame:
        """
        Remove outliers using Z-score method
        """
        cleaned_df = df.copy()
        
        for column in cleaned_df.select_dtypes(include=[np.number]).columns:
            z_scores = np.abs((cleaned_df[column] - cleaned_df[column].mean()) / cleaned_df[column].std())
            # Cap values beyond threshold
            max_val = cleaned_df[column].mean() + threshold * cleaned_df[column].std()
            min_val = cleaned_df[column].mean() - threshold * cleaned_df[column].std()
            cleaned_df[column] = np.where(cleaned_df[column] > max_val, max_val, cleaned_df[column])
            cleaned_df[column] = np.where(cleaned_df[column] < min_val, min_val, cleaned_df[column])
        
        return cleaned_df
    
    @staticmethod
    def calculate_returns(df: pd.DataFrame, period: int = 1) -> pd.DataFrame:
        """
        Calculate returns over specified period
        """
        if 'Close' not in df.columns:
            raise ValueError("DataFrame must contain 'Close' column")
        
        returns_df = pd.DataFrame(index=df.index)
        returns_df['return'] = df['Close'].pct_change(periods=period)
        returns_df['log_return'] = np.log(df['Close'] / df['Close'].shift(period))
        
        # Remove NaN values
        returns_df = returns_df.dropna()
        
        return returns_df
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, window: int = 20) -> pd.Series:
        """
        Calculate rolling volatility
        """
        if 'Close' not in df.columns:
            raise ValueError("DataFrame must contain 'Close' column")
        
        returns = df['Close'].pct_change()
        volatility = returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
        
        return volatility
    
    @staticmethod
    def calculate_moving_averages(df: pd.DataFrame, windows: List[int] = None) -> pd.DataFrame:
        """
        Calculate multiple moving averages
        """
        if windows is None:
            windows = [5, 10, 20, 50, 200]
        
        ma_df = pd.DataFrame(index=df.index)
        
        for window in windows:
            ma_df[f'SMA_{window}'] = df['Close'].rolling(window=window).mean()
            ma_df[f'EMA_{window}'] = df['Close'].ewm(span=window).mean()
        
        return ma_df
    
    @staticmethod
    def detect_trend(df: pd.DataFrame, short_window: int = 20, long_window: int = 50) -> pd.Series:
        """
        Detect market trend using moving averages
        """
        if 'Close' not in df.columns:
            raise ValueError("DataFrame must contain 'Close' column")
        
        df_ma = DataProcessor.calculate_moving_averages(df, [short_window, long_window])
        
        # Trend: 1 for uptrend, -1 for downtrend, 0 for neutral
        trend = np.where(
            df_ma[f'SMA_{short_window}'] > df_ma[f'SMA_{long_window}'], 1, 
            np.where(df_ma[f'SMA_{short_window}'] < df_ma[f'SMA_{long_window}'], -1, 0)
        )
        
        return pd.Series(trend, index=df.index, name='trend')
    
    @staticmethod
    def resample_data(df: pd.DataFrame, freq: str = 'W') -> pd.DataFrame:
        """
        Resample data to different frequency
        """
        if freq not in ['D', 'W', 'M', 'Q', 'Y']:
            raise ValueError("Frequency must be one of: 'D', 'W', 'M', 'Q', 'Y'")
        
        resampled = df.resample(freq).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })
        
        return resampled.dropna()
    
    @staticmethod
    def calculate_correlation_matrix(returns_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation matrix for multiple assets
        """
        if returns_data.empty:
            return pd.DataFrame()
        
        # Ensure we're working with returns data
        if not all(col.endswith('_return') for col in returns_data.columns):
            # Assume these are price data, calculate returns
            returns_data = returns_data.pct_change().dropna()
        
        correlation_matrix = returns_data.corr()
        
        return correlation_matrix
    
    @staticmethod
    def calculate_beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
        """
        Calculate beta coefficient for an asset relative to market
        """
        # Align the series by date
        aligned_data = pd.concat([asset_returns, market_returns], axis=1, join='inner')
        aligned_data.columns = ['asset', 'market']
        aligned_data = aligned_data.dropna()
        
        if len(aligned_data) < 30:
            return 1.0  # Default beta for insufficient data
        
        # Calculate covariance and variance
        covariance = aligned_data[['asset', 'market']].cov().iloc[0, 1]
        market_variance = aligned_data['market'].var()
        
        beta = covariance / market_variance if market_variance != 0 else 1.0
        
        return beta
    
    @staticmethod
    def detect_seasonality(df: pd.DataFrame, column: str = 'Close') -> Dict:
        """
        Detect seasonal patterns in time series data
        """
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        # Extract time components
        df_copy = df.copy()
        df_copy['year'] = df_copy.index.year
        df_copy['month'] = df_copy.index.month
        df_copy['day'] = df_copy.index.day
        df_copy['dayofweek'] = df_copy.index.dayofweek
        
        # Calculate monthly averages
        monthly_avg = df_copy.groupby('month')[column].mean()
        
        # Calculate day-of-week averages
        dow_avg = df_copy.groupby('dayofweek')[column].mean()
        
        return {
            'monthly_pattern': monthly_avg.to_dict(),
            'day_of_week_pattern': dow_avg.to_dict(),
            'seasonal_strength': monthly_avg.std() / monthly_avg.mean() if monthly_avg.mean() != 0 else 0
        }
    
    @staticmethod
    def calculate_rolling_metrics(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        Calculate various rolling metrics for technical analysis
        """
        metrics_df = pd.DataFrame(index=df.index)
        
        if 'Close' not in df.columns:
            return metrics_df
        
        # Rolling returns
        metrics_df['rolling_return'] = df['Close'].pct_change(window)
        
        # Rolling volatility
        returns = df['Close'].pct_change()
        metrics_df['rolling_volatility'] = returns.rolling(window).std() * np.sqrt(252)
        
        # Rolling Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02 / 252
        excess_returns = returns - risk_free_rate
        metrics_df['rolling_sharpe'] = (
            excess_returns.rolling(window).mean() / 
            returns.rolling(window).std() * np.sqrt(252)
        ).replace([np.inf, -np.inf], np.nan)
        
        # Maximum drawdown
        rolling_max = df['Close'].rolling(window, min_periods=1).max()
        metrics_df['drawdown'] = (df['Close'] - rolling_max) / rolling_max
        
        return metrics_df.dropna()
    
    @staticmethod
    def prepare_features_for_ml(df: pd.DataFrame, target_col: str = 'future_return') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for machine learning models
        """
        features_df = pd.DataFrame(index=df.index)
        
        if 'Close' not in df.columns:
            return features_df, pd.Series()
        
        # Price-based features
        features_df['price'] = df['Close']
        features_df['high_low_ratio'] = df['High'] / df['Low']
        features_df['open_close_ratio'] = df['Open'] / df['Close']
        
        # Volume features
        if 'Volume' in df.columns:
            features_df['volume'] = df['Volume']
            features_df['volume_sma'] = df['Volume'].rolling(10).mean()
            features_df['volume_ratio'] = df['Volume'] / features_df['volume_sma']
        
        # Technical indicators
        returns = df['Close'].pct_change()
        features_df['returns'] = returns
        features_df['returns_lag1'] = returns.shift(1)
        features_df['returns_lag2'] = returns.shift(2)
        features_df['returns_lag3'] = returns.shift(3)
        
        # Volatility features
        features_df['volatility'] = returns.rolling(10).std()
        features_df['volatility_ratio'] = features_df['volatility'] / features_df['volatility'].rolling(20).mean()
        
        # Moving average features
        features_df['sma_10'] = df['Close'].rolling(10).mean()
        features_df['sma_20'] = df['Close'].rolling(20).mean()
        features_df['sma_50'] = df['Close'].rolling(50).mean()
        features_df['price_vs_sma_10'] = df['Close'] / features_df['sma_10']
        features_df['price_vs_sma_20'] = df['Close'] / features_df['sma_20']
        
        # Create target variable (future return)
        target = df['Close'].pct_change(5).shift(-5)  # 5-day future return
        
        # Remove NaN values
        features_df = features_df.dropna()
        target = target.reindex(features_df.index)
        
        return features_df, target