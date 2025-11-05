"""
Model Training Pipeline for Bulk Stock Data
Pre-trains LSTM models on multiple stocks for faster predictions
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

from .stock_data_fetcher import (
    download_all_indian_stocks, 
    download_all_us_stocks,
    calculate_technical_indicators
)

try:
    from tensorflow import keras
    from keras.models import Sequential, load_model
    from keras.layers import LSTM, Dense, Dropout
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("Warning: TensorFlow/Keras not available")

from sklearn.preprocessing import MinMaxScaler


class ModelTrainer:
    """Handles bulk training and model persistence"""
    
    def __init__(self, model_dir="models/pretrained"):
        """
        Initialize model trainer
        
        Args:
            model_dir: Directory to save trained models
        """
        self.model_dir = model_dir
        self.lookback = 30
        self.features = ['Close', 'Volume', 'MA5', 'MA10', 'MA20', 
                        'Price_Change', 'Price_Range', 'Volume_Change', 'RSI']
        
        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        os.makedirs(f"{model_dir}/scalers", exist_ok=True)
        os.makedirs(f"{model_dir}/metadata", exist_ok=True)
        
    def prepare_stock_data(self, df):
        """
        Prepare single stock data for training
        
        Args:
            df: Stock DataFrame
            
        Returns:
            X, y, feature_scaler, target_scaler (or None if insufficient data)
        """
        try:
            # Ensure we have required columns
            if 'Close' not in df.columns:
                return None
            
            # Calculate indicators if not present
            if 'MA5' not in df.columns:
                df = calculate_technical_indicators(df)
                df = df.dropna()
            
            # Check if we have enough data
            if len(df) < self.lookback + 50:
                return None
            
            # Extract features
            feature_data = df[self.features].values
            
            # Check for infinity or NaN values
            if not np.isfinite(feature_data).all():
                print(f"Warning: Non-finite values detected. Cleaning data...")
                # Replace infinity with NaN, then forward fill, then backward fill
                feature_data = np.where(np.isfinite(feature_data), feature_data, np.nan)
                feature_df = pd.DataFrame(feature_data, columns=self.features)
                # Use ffill() and bfill() instead of deprecated method parameter
                feature_df = feature_df.ffill().bfill().fillna(0)
                feature_data = feature_df.values
                
                # Final check
                if not np.isfinite(feature_data).all():
                    print(f"Error: Still contains non-finite values after cleaning")
                    return None
            
            # Scale features
            feature_scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_features = feature_scaler.fit_transform(feature_data)
            
            # Scale target
            target_scaler = MinMaxScaler(feature_range=(0, 1))
            prices = df['Close'].values.reshape(-1, 1)
            scaled_prices = target_scaler.fit_transform(prices)
            
            # Create sequences
            X, y = [], []
            for i in range(self.lookback, len(scaled_features)):
                X.append(scaled_features[i-self.lookback:i])
                y.append(scaled_prices[i, 0])
            
            X, y = np.array(X), np.array(y)
            
            return X, y, feature_scaler, target_scaler
            
        except Exception as e:
            print(f"Error preparing data: {e}")
            return None
    
    def build_model(self):
        """Build LSTM model architecture"""
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=(self.lookback, len(self.features))),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=25, activation='relu'),
            Dense(units=1)
        ])
        
        model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
        return model
    
    def train_single_stock(self, symbol, df, epochs=10, batch_size=32):
        """
        Train model for a single stock
        
        Args:
            symbol: Stock symbol
            df: Stock DataFrame
            epochs: Training epochs
            batch_size: Batch size
            
        Returns:
            Training metrics or None if failed
        """
        try:
            # Prepare data
            result = self.prepare_stock_data(df)
            if result is None:
                return None
            
            X, y, feature_scaler, target_scaler = result
            
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Build and train model
            model = self.build_model()
            
            # Adapt batch size
            actual_batch_size = min(batch_size, max(8, len(X_train) // 10))
            
            history = model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=actual_batch_size,
                verbose=0,
                validation_split=0.05
            )
            
            # Evaluate on test set
            test_loss, test_mae = model.evaluate(X_test, y_test, verbose=0)
            
            # Save model and scalers
            safe_symbol = symbol.replace('.', '_').replace('&', 'AND')
            model_path = f"{self.model_dir}/{safe_symbol}.keras"
            scaler_path = f"{self.model_dir}/scalers/{safe_symbol}.pkl"
            metadata_path = f"{self.model_dir}/metadata/{safe_symbol}.json"
            
            # Save model
            model.save(model_path)
            
            # Save scalers
            with open(scaler_path, 'wb') as f:
                pickle.dump({
                    'feature_scaler': feature_scaler,
                    'target_scaler': target_scaler
                }, f)
            
            # Save metadata
            metadata = {
                'symbol': symbol,
                'trained_date': datetime.now().isoformat(),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'test_loss': float(test_loss),
                'test_mae': float(test_mae),
                'final_train_loss': float(history.history['loss'][-1]),
                'epochs': epochs,
                'lookback': self.lookback,
                'features': self.features
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return metadata
            
        except Exception as e:
            print(f"Error training {symbol}: {e}")
            return None
    
    def train_all_stocks(self, stock_data, market_name="stocks", epochs=10, batch_size=32):
        """
        Train models for all stocks in bulk
        
        Args:
            stock_data: Dictionary of {symbol: DataFrame}
            market_name: Name for logging (e.g., "Indian", "US")
            epochs: Training epochs per stock
            batch_size: Batch size
            
        Returns:
            Training summary
        """
        print(f"\n{'='*60}")
        print(f"Training {len(stock_data)} {market_name} stocks")
        print(f"{'='*60}\n")
        
        successful = []
        failed = []
        
        for symbol, df in tqdm(stock_data.items(), desc=f"Training {market_name}"):
            result = self.train_single_stock(symbol, df, epochs=epochs, batch_size=batch_size)
            
            if result is not None:
                successful.append(result)
            else:
                failed.append(symbol)
        
        summary = {
            'market': market_name,
            'total_stocks': len(stock_data),
            'successful': len(successful),
            'failed': len(failed),
            'failed_symbols': failed,
            'training_date': datetime.now().isoformat(),
            'models': successful
        }
        
        # Save summary
        summary_path = f"{self.model_dir}/training_summary_{market_name.lower()}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully trained: {len(successful)} stocks")
        print(f"❌ Failed: {len(failed)} stocks")
        if len(stock_data) > 0:
            print(f"📊 Success rate: {len(successful)/len(stock_data)*100:.1f}%")
        else:
            print(f"📊 Success rate: N/A (no stocks to train)")
        print(f"{'='*60}\n")
        
        return summary
    
    def load_pretrained_model(self, symbol):
        """
        Load pre-trained model and scalers for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            (model, feature_scaler, target_scaler, metadata) or None if not found
        """
        try:
            safe_symbol = symbol.replace('.', '_').replace('&', 'AND')
            model_path = f"{self.model_dir}/{safe_symbol}.keras"
            scaler_path = f"{self.model_dir}/scalers/{safe_symbol}.pkl"
            metadata_path = f"{self.model_dir}/metadata/{safe_symbol}.json"
            
            # Check if files exist
            if not all(os.path.exists(p) for p in [model_path, scaler_path, metadata_path]):
                return None
            
            # Load model
            model = load_model(model_path)
            
            # Load scalers
            with open(scaler_path, 'rb') as f:
                scalers = pickle.load(f)
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            return (
                model, 
                scalers['feature_scaler'], 
                scalers['target_scaler'], 
                metadata
            )
            
        except Exception as e:
            print(f"Error loading model for {symbol}: {e}")
            return None
    
    def get_training_status(self):
        """
        Get status of all trained models
        
        Returns:
            Dictionary with training statistics
        """
        try:
            indian_summary_path = f"{self.model_dir}/training_summary_indian.json"
            us_summary_path = f"{self.model_dir}/training_summary_us.json"
            
            status = {
                'model_directory': self.model_dir,
                'indian_stocks': None,
                'us_stocks': None,
                'total_models': 0
            }
            
            if os.path.exists(indian_summary_path):
                with open(indian_summary_path, 'r') as f:
                    status['indian_stocks'] = json.load(f)
                    status['total_models'] += status['indian_stocks']['successful']
            
            if os.path.exists(us_summary_path):
                with open(us_summary_path, 'r') as f:
                    status['us_stocks'] = json.load(f)
                    status['total_models'] += status['us_stocks']['successful']
            
            return status
            
        except Exception as e:
            print(f"Error getting training status: {e}")
            return None


def run_full_training_pipeline(period="1y", epochs=10):
    """
    Complete training pipeline: Download and train all stocks
    
    Args:
        period: Historical data period
        epochs: Training epochs per stock
        
    Returns:
        Complete training report
    """
    if not KERAS_AVAILABLE:
        return {
            'success': False,
            'error': 'TensorFlow/Keras not available'
        }
    
    print("\n" + "="*60)
    print("🚀 STARTING FULL TRAINING PIPELINE")
    print("="*60 + "\n")
    
    trainer = ModelTrainer()
    report = {
        'success': True,
        'start_time': datetime.now().isoformat(),
        'period': period,
        'epochs': epochs
    }
    
    try:
        # Step 1: Download Indian stocks
        print("📥 Step 1/4: Downloading Indian stocks...")
        indian_data = download_all_indian_stocks(period=period)
        report['indian_downloaded'] = len(indian_data)
        
        # Step 2: Train Indian stocks
        print("\n🔥 Step 2/4: Training Indian stocks...")
        indian_summary = trainer.train_all_stocks(indian_data, "Indian", epochs=epochs)
        report['indian_summary'] = indian_summary
        
        # Step 3: Download US stocks
        print("\n📥 Step 3/4: Downloading US stocks...")
        us_data = download_all_us_stocks(period=period)
        report['us_downloaded'] = len(us_data)
        
        # Step 4: Train US stocks
        print("\n🔥 Step 4/4: Training US stocks...")
        us_summary = trainer.train_all_stocks(us_data, "US", epochs=epochs)
        report['us_summary'] = us_summary
        
        # Final summary
        report['end_time'] = datetime.now().isoformat()
        report['total_models'] = indian_summary['successful'] + us_summary['successful']
        report['total_downloaded'] = len(indian_data) + len(us_data)
        
        print("\n" + "="*60)
        print("✅ TRAINING PIPELINE COMPLETED!")
        print("="*60)
        print(f"📊 Total stocks downloaded: {report['total_downloaded']}")
        print(f"🎯 Total models trained: {report['total_models']}")
        print(f"🇮🇳 Indian stocks: {indian_summary['successful']}/{len(indian_data)}")
        print(f"🇺🇸 US stocks: {us_summary['successful']}/{len(us_data)}")
        print("="*60 + "\n")
        
        # Save complete report
        report_path = f"{trainer.model_dir}/complete_training_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
        
    except Exception as e:
        report['success'] = False
        report['error'] = str(e)
        print(f"\n❌ Training pipeline failed: {e}")
        return report
