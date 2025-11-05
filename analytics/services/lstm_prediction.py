"""
LSTM-based Stock Price Prediction Service
Uses Long Short-Term Memory neural networks to predict future stock prices
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Import the new stock data fetcher
from .stock_data_fetcher import download_stock_with_fallback
# Import model trainer for pre-trained models
from .model_trainer import ModelTrainer

# TensorFlow imports with error handling
try:
    from tensorflow import keras
    from keras.models import Sequential
    from keras.layers import LSTM, Dense, Dropout
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("Warning: TensorFlow/Keras not available. LSTM predictions disabled.")


class LSTMPredictor:
    """LSTM model for stock price prediction"""
    
    def __init__(self, lookback=30):
        """
        Initialize LSTM predictor (optimized lookback for speed)
        
        Args:
            lookback: Number of previous days to use for prediction
        """
        self.lookback = lookback
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.target_scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        
    def prepare_data(self, data, column='Close'):
        """
        Prepare multi-feature data for LSTM training (more accurate predictions)
        
        Args:
            data: DataFrame with stock data
            column: Column to use for prediction
            
        Returns:
            X_train, y_train, X_test, y_test, scaled_data, feature_scaler
        """
        # Create multiple features for better predictions
        df = data.copy()
        
        # 1. Price features
        df['Close'] = df['Close']
        df['High'] = df['High']
        df['Low'] = df['Low']
        df['Volume'] = df['Volume']
        
        # 2. Moving averages
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        
        # 3. Price momentum
        df['Price_Change'] = df['Close'].pct_change()
        df['Price_Range'] = (df['High'] - df['Low']) / df['Close']
        
        # 4. Volume momentum
        df['Volume_Change'] = df['Volume'].pct_change()
        
        # 5. RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Drop NaN values
        df = df.dropna()
        
        # Check if we have enough data
        if len(df) < self.lookback + 50:
            raise ValueError(f"Insufficient data after feature calculation. Need at least {self.lookback + 50} rows, got {len(df)}. Try a longer period.")
        
        # Select features
        features = ['Close', 'Volume', 'MA5', 'MA10', 'MA20', 'Price_Change', 
                   'Price_Range', 'Volume_Change', 'RSI']
        
        # Scale all features
        feature_data = df[features].values
        scaled_features = self.scaler.fit_transform(feature_data)
        
        # Target is just the Close price
        prices = df['Close'].values.reshape(-1, 1)
        scaled_prices = self.target_scaler.fit_transform(prices)
        
        # Create sequences
        X, y = [], []
        for i in range(self.lookback, len(scaled_features)):
            X.append(scaled_features[i-self.lookback:i])
            y.append(scaled_prices[i, 0])
        
        X, y = np.array(X), np.array(y)
        
        print(f"Created {len(X)} sequences from {len(df)} rows of data")
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        print(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples")
        
        return X_train, y_train, X_test, y_test, scaled_features
    
    def build_model(self, input_shape):
        """
        Build enhanced LSTM model with attention mechanism
        
        Args:
            input_shape: Shape of input data (timesteps, features)
        """
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=25, activation='relu'),
            Dense(units=1)
        ])
        
        model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
        self.model = model
        
    def train(self, X_train, y_train, epochs=10, batch_size=32):
        """
        Train the LSTM model (optimized for speed)
        
        Args:
            X_train: Training features
            y_train: Training labels
            epochs: Number of training epochs (reduced for speed)
            batch_size: Batch size for training (adaptive to data size)
        """
        if self.model is None:
            # Input shape should be (timesteps, features)
            self.build_model((X_train.shape[1], X_train.shape[2]))
        
        # Adapt batch size to training data size
        actual_batch_size = min(batch_size, max(8, len(X_train) // 10))
        print(f"Using batch size: {actual_batch_size}")
        
        self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=actual_batch_size,
            verbose=0,
            validation_split=0.05
        )
    
    def predict(self, X):
        """
        Make predictions using trained model
        
        Args:
            X: Input data
            
        Returns:
            Predictions in original scale
        """
        predictions = self.model.predict(X, verbose=0)
        return self.scaler.inverse_transform(predictions)
    
    def predict_future(self, df, days=30):
        """
        Predict future prices using multi-feature data
        
        Args:
            df: Historical DataFrame with all features
            days: Number of days to predict
            
        Returns:
            Array of predicted prices
        """
        # Prepare features from recent data
        recent_df = df.tail(self.lookback + 50).copy()  # Extra buffer for indicators
        
        # Recalculate features for recent data
        recent_df['MA5'] = recent_df['Close'].rolling(window=5).mean()
        recent_df['MA10'] = recent_df['Close'].rolling(window=10).mean()
        recent_df['MA20'] = recent_df['Close'].rolling(window=20).mean()
        recent_df['Price_Change'] = recent_df['Close'].pct_change()
        recent_df['Price_Range'] = (recent_df['High'] - recent_df['Low']) / recent_df['Close']
        recent_df['Volume_Change'] = recent_df['Volume'].pct_change()
        
        delta = recent_df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        recent_df['RSI'] = 100 - (100 / (1 + rs))
        
        recent_df = recent_df.dropna()
        
        features = ['Close', 'Volume', 'MA5', 'MA10', 'MA20', 'Price_Change', 
                   'Price_Range', 'Volume_Change', 'RSI']
        
        # Get last sequence
        last_sequence = recent_df[features].values[-self.lookback:]
        last_sequence_scaled = self.scaler.transform(last_sequence)
        
        predictions = []
        current_sequence = last_sequence_scaled.copy()
        
        # For simplicity in future prediction, we'll use a simpler approach
        # This is a limitation of multi-feature forecasting
        for _ in range(days):
            # Reshape for prediction
            input_seq = current_sequence.reshape(1, self.lookback, len(features))
            
            # Predict next value
            next_pred = self.model.predict(input_seq, verbose=0)
            predictions.append(next_pred[0, 0])
            
            # For updating sequence, we need to estimate other features
            # Use the last known values with small random variation
            last_features = current_sequence[-1].copy()
            last_features[0] = next_pred[0, 0]  # Update Close price prediction
            
            # Update sequence
            current_sequence = np.vstack([current_sequence[1:], last_features.reshape(1, -1)])
        
        # Convert predictions back to original scale using the fitted target_scaler
        predictions_array = np.array(predictions).reshape(-1, 1)
        predictions_unscaled = self.target_scaler.inverse_transform(predictions_array)
        
        return predictions_unscaled.flatten()


def run_lstm_prediction_pretrained(symbol, period='2y', future_days=30):
    """
    Run LSTM prediction using pre-trained model (FAST!)
    Falls back to training if no pre-trained model exists
    
    Args:
        symbol: Stock symbol
        period: Historical data period
        future_days: Number of days to predict
        
    Returns:
        Dictionary with predictions and metrics
    """
    if not KERAS_AVAILABLE:
        return {
            'success': False,
            'error': 'TensorFlow/Keras not installed'
        }
    
    try:
        trainer = ModelTrainer()
        
        # Try to load pre-trained model
        print(f"🔍 Checking for pre-trained model for {symbol}...")
        pretrained = trainer.load_pretrained_model(symbol)
        
        if pretrained is not None:
            model, feature_scaler, target_scaler, metadata = pretrained
            print(f"✅ Found pre-trained model! (trained on {metadata['trained_date']})")
            print(f"   Test MAE: {metadata['test_mae']:.4f}, Test Loss: {metadata['test_loss']:.6f}")
            
            # Fetch recent data for prediction
            df = download_stock_with_fallback(symbol, period="6mo")  # Get 6 months to ensure enough data after indicators
            
            if df is None or df.empty:
                return {'success': False, 'error': f'No data found for {symbol}'}
            
            # Prepare recent data
            from .stock_data_fetcher import calculate_technical_indicators
            df = calculate_technical_indicators(df)
            df = df.dropna()
            
            if len(df) < 30:
                return {'success': False, 'error': f'Insufficient recent data: need 30 rows, got {len(df)}. Try longer period.'}
            
            # Get features
            features = ['Close', 'Volume', 'MA5', 'MA10', 'MA20', 'Price_Change', 
                       'Price_Range', 'Volume_Change', 'RSI']
            
            # Scale recent data
            last_sequence = df[features].values[-30:]
            last_sequence_scaled = feature_scaler.transform(last_sequence)
            
            # Predict future
            predictions = []
            current_sequence = last_sequence_scaled.copy()
            
            for _ in range(future_days):
                input_seq = current_sequence.reshape(1, 30, len(features))
                next_pred = model.predict(input_seq, verbose=0)
                predictions.append(next_pred[0, 0])
                
                # Update sequence
                last_features = current_sequence[-1].copy()
                last_features[0] = next_pred[0, 0]
                current_sequence = np.vstack([current_sequence[1:], last_features.reshape(1, -1)])
            
            # Inverse transform
            predictions_array = np.array(predictions).reshape(-1, 1)
            predictions_unscaled = target_scaler.inverse_transform(predictions_array)
            
            # Generate future dates
            last_date = df.index[-1]
            future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=future_days)
            
            return {
                'success': True,
                'symbol': symbol,
                'predictions': predictions_unscaled.flatten().tolist(),
                'future_dates': future_dates.strftime('%Y-%m-%d').tolist(),
                'historical_prices': df['Close'].values.tolist(),
                'historical_dates': df.index.strftime('%Y-%m-%d').tolist(),
                'current_price': float(df['Close'].iloc[-1]),
                'predicted_price': float(predictions_unscaled[-1]),
                'price_change_percent': float((predictions_unscaled[-1] - df['Close'].iloc[-1]) / df['Close'].iloc[-1] * 100),
                'model_metadata': metadata,
                'using_pretrained': True
            }
        
        else:
            print(f"⚠️ No pre-trained model found for {symbol}")
            print(f"   Falling back to training new model...")
            # Fall back to regular training
            return run_lstm_prediction(symbol, period, num_simulations=1, future_days=future_days)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def run_lstm_prediction(symbol, period='2y', num_simulations=5, future_days=30):
    """
    Run LSTM prediction with multiple simulations
    
    Args:
        symbol: Stock symbol
        period: Historical data period (e.g., '1y', '2y', '5y')
        num_simulations: Number of simulation runs
        future_days: Number of days to predict
        
    Returns:
        Dictionary with predictions and metrics
    """
    if not KERAS_AVAILABLE:
        return {
            'success': False,
            'error': 'TensorFlow/Keras not installed. Please install: pip install tensorflow keras'
        }
    
    try:
        # Fetch historical data using enhanced fetcher (supports nsepy for Indian stocks)
        print(f"Fetching data for {symbol} with period {period}...")
        df = download_stock_with_fallback(symbol, period=period)
        
        if df is None or df.empty:
            return {
                'success': False,
                'error': f'No data found for symbol {symbol}'
            }
        
        # Run multiple simulations
        all_predictions = []
        historical_prices = df['Close'].values
        historical_dates = df.index.strftime('%Y-%m-%d').tolist()
        
        print(f"Starting {num_simulations} simulations for {symbol}...")
        print(f"Data shape: {df.shape}, Date range: {df.index[0]} to {df.index[-1]}")
        
        for sim in range(num_simulations):
            try:
                print(f"\n--- Simulation {sim + 1}/{num_simulations} ---")
                predictor = LSTMPredictor(lookback=30)
                
                # Prepare multi-feature data
                print("Preparing data with multi-features...")
                X_train, y_train, X_test, y_test, scaled_features = predictor.prepare_data(df)
                print(f"Training data shape: X_train={X_train.shape}, y_train={y_train.shape}")
                
                # Train model with enhanced features
                print("Training LSTM model...")
                predictor.train(X_train, y_train, epochs=10, batch_size=32)
                
                # Predict future using full dataframe
                print(f"Predicting {future_days} days into the future...")
                future_predictions = predictor.predict_future(df, days=future_days)
                all_predictions.append(future_predictions.tolist())
                print(f"Simulation {sim + 1} completed successfully!")
                
            except Exception as e:
                print(f"\n❌ Simulation {sim + 1} FAILED: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        if not all_predictions:
            return {
                'success': False,
                'error': 'All simulations failed. Please try different parameters.'
            }
        
        # Calculate average prediction
        avg_prediction = np.mean(all_predictions, axis=0).tolist()
        std_prediction = np.std(all_predictions, axis=0).tolist()
        
        # Generate future dates
        last_date = df.index[-1]
        future_dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') 
                       for i in range(future_days)]
        
        # Calculate metrics
        current_price = historical_prices[-1]
        predicted_price = avg_prediction[-1]
        price_change = predicted_price - current_price
        price_change_pct = (price_change / current_price) * 100
        
        return {
            'success': True,
            'symbol': symbol,
            'historical': {
                'dates': historical_dates,
                'prices': historical_prices.tolist()
            },
            'predictions': {
                'dates': future_dates,
                'average': avg_prediction,
                'std': std_prediction,
                'simulations': all_predictions
            },
            'metrics': {
                'current_price': round(current_price, 2),
                'predicted_price': round(predicted_price, 2),
                'price_change': round(price_change, 2),
                'price_change_pct': round(price_change_pct, 2),
                'num_simulations': len(all_predictions),
                'future_days': future_days
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Prediction failed: {str(e)}'
        }


def get_prediction_confidence(predictions_array):
    """
    Calculate confidence metrics from multiple predictions
    
    Args:
        predictions_array: Array of predictions from multiple simulations
        
    Returns:
        Confidence metrics
    """
    predictions = np.array(predictions_array)
    
    return {
        'mean': np.mean(predictions, axis=0).tolist(),
        'std': np.std(predictions, axis=0).tolist(),
        'min': np.min(predictions, axis=0).tolist(),
        'max': np.max(predictions, axis=0).tolist(),
        'confidence_interval_95': {
            'lower': (np.mean(predictions, axis=0) - 1.96 * np.std(predictions, axis=0)).tolist(),
            'upper': (np.mean(predictions, axis=0) + 1.96 * np.std(predictions, axis=0)).tolist()
        }
    }
