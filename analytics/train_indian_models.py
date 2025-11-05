"""
Train LSTM Models on Indian (NSE) Stocks
Uses the downloaded NSE bhavcopy data to pre-train models
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score
import pickle

class IndianStockTrainer:
    """Train LSTM models on Indian stock data"""
    
    def __init__(self, data_file: str, output_dir: str = "models/pretrained"):
        self.data_file = data_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Model parameters
        self.sequence_length = 60  # 60 days of historical data
        self.lstm_units = 50
        self.epochs = 10
        self.batch_size = 32
        
        # Load data
        self.load_data()
    
    def setup_logging(self):
        """Setup logging"""
        log_file = self.output_dir / "training.log"
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logging.info("🚀 Indian Stock Model Trainer started")
    
    def load_data(self):
        """Load NSE stock data"""
        logging.info(f"📥 Loading data from {self.data_file}")
        
        try:
            if self.data_file.endswith('.parquet'):
                self.df = pd.read_parquet(self.data_file)
            else:
                self.df = pd.read_csv(self.data_file)
            
            # Ensure DATE is datetime
            self.df['DATE'] = pd.to_datetime(self.df['DATE'])
            
            # Sort by symbol and date
            self.df = self.df.sort_values(['SYMBOL', 'DATE'])
            
            logging.info(f"✅ Loaded {len(self.df):,} records")
            logging.info(f"   Unique stocks: {self.df['SYMBOL'].nunique()}")
            logging.info(f"   Date range: {self.df['DATE'].min().date()} to {self.df['DATE'].max().date()}")
            
        except Exception as e:
            logging.error(f"❌ Error loading data: {e}")
            raise
    
    def prepare_data(self, stock_data: pd.DataFrame):
        """Prepare data for LSTM training"""
        # Use CLOSE prices
        prices = stock_data['CLOSE'].values.reshape(-1, 1)
        
        # Scale data
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(prices)
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i, 0])
            y.append(scaled_data[i, 0])
        
        X = np.array(X)
        y = np.array(y)
        
        # Reshape X for LSTM [samples, time steps, features]
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))
        
        return X, y, scaler
    
    def build_model(self, input_shape):
        """Build LSTM model"""
        model = keras.Sequential([
            keras.layers.LSTM(units=self.lstm_units, return_sequences=True, 
                            input_shape=input_shape),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(units=self.lstm_units, return_sequences=False),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(units=25),
            keras.layers.Dense(units=1)
        ])
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model
    
    def train_stock(self, symbol: str, min_data_points: int = 200):
        """Train model for a single stock"""
        try:
            # Get stock data
            stock_data = self.df[self.df['SYMBOL'] == symbol].copy()
            
            # Check if enough data
            if len(stock_data) < min_data_points:
                logging.warning(f"⚠️  {symbol}: Not enough data ({len(stock_data)} < {min_data_points})")
                return None
            
            # Remove rows with missing CLOSE prices
            stock_data = stock_data.dropna(subset=['CLOSE'])
            
            if len(stock_data) < min_data_points:
                logging.warning(f"⚠️  {symbol}: Not enough valid data after cleaning")
                return None
            
            # Prepare data
            X, y, scaler = self.prepare_data(stock_data)
            
            if len(X) < 50:  # Need at least 50 samples for training
                logging.warning(f"⚠️  {symbol}: Not enough sequences ({len(X)} < 50)")
                return None
            
            # Split into train/test
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Build and train model
            model = self.build_model((X_train.shape[1], 1))
            
            # Train with early stopping
            early_stop = keras.callbacks.EarlyStopping(
                monitor='loss',
                patience=3,
                restore_best_weights=True
            )
            
            history = model.fit(
                X_train, y_train,
                epochs=self.epochs,
                batch_size=self.batch_size,
                validation_split=0.1,
                callbacks=[early_stop],
                verbose=0
            )
            
            # Evaluate
            predictions = model.predict(X_test, verbose=0)
            mse = mean_squared_error(y_test, predictions)
            r2 = r2_score(y_test, predictions)
            
            # Save model
            model_file = self.output_dir / f"{symbol}.keras"
            model.save(model_file)
            
            # Save scaler
            scaler_file = self.output_dir / f"{symbol}_scaler.pkl"
            with open(scaler_file, 'wb') as f:
                pickle.dump(scaler, f)
            
            # Save metadata
            metadata = {
                'symbol': symbol,
                'market': 'NSE',
                'trained_on': datetime.now().isoformat(),
                'data_points': len(stock_data),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'mse': float(mse),
                'r2_score': float(r2),
                'sequence_length': self.sequence_length,
                'epochs_trained': len(history.history['loss']),
                'final_loss': float(history.history['loss'][-1])
            }
            
            metadata_file = self.output_dir / f"{symbol}_metadata.pkl"
            with open(metadata_file, 'wb') as f:
                pickle.dump(metadata, f)
            
            logging.info(f"✅ {symbol}: R²={r2:.4f}, MSE={mse:.6f}, Data={len(stock_data)}")
            
            return metadata
            
        except Exception as e:
            logging.error(f"❌ {symbol}: Training failed - {str(e)[:100]}")
            return None
    
    def train_all_stocks(self, top_n: int = 100, min_data_points: int = 200):
        """Train models for top N stocks by trading volume"""
        logging.info(f"🎯 Training models for top {top_n} stocks")
        
        # Check if we have any data
        if len(self.df) == 0:
            logging.error("❌ No data available for training!")
            logging.error("   The dataset is empty (0 records)")
            return {
                'successful': [],
                'failed': [],
                'total': 0,
                'error': 'No data available'
            }
        
        # Calculate total trading volume per stock
        stock_volumes = (self.df.groupby('SYMBOL')['VOLUME']
                        .sum()
                        .sort_values(ascending=False))
        
        # Check if we have any stocks
        if len(stock_volumes) == 0:
            logging.error("❌ No stocks found in dataset!")
            return {
                'successful': [],
                'failed': [],
                'total': 0,
                'error': 'No stocks found'
            }
        
        # Get top stocks
        top_stocks = stock_volumes.head(top_n).index.tolist()
        
        if len(top_stocks) == 0:
            logging.error("❌ No stocks selected for training!")
            return {
                'successful': [],
                'failed': [],
                'total': 0,
                'error': 'No stocks selected'
            }
        
        logging.info(f"📊 Selected {len(top_stocks)} stocks for training")
        logging.info(f"   Top 10: {', '.join(top_stocks[:10])}")
        
        # Train each stock
        results = {
            'successful': [],
            'failed': [],
            'total': len(top_stocks)
        }
        
        for i, symbol in enumerate(top_stocks, 1):
            progress = (i / len(top_stocks)) * 100
            logging.info(f"📈 Progress: {i}/{len(top_stocks)} ({progress:.1f}%) - Training {symbol}")
            
            metadata = self.train_stock(symbol, min_data_points)
            
            if metadata is not None:
                results['successful'].append(metadata)
            else:
                results['failed'].append(symbol)
        
        # Save overall results
        results_file = self.output_dir / "indian_stocks_training_results.pkl"
        with open(results_file, 'wb') as f:
            pickle.dump(results, f)
        
        # Generate summary
        self.generate_summary(results)
        
        return results
    
    def generate_summary(self, results: dict):
        """Generate training summary"""
        summary = []
        summary.append("=" * 70)
        summary.append("INDIAN STOCKS TRAINING SUMMARY")
        summary.append("=" * 70)
        summary.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"Total stocks attempted: {results['total']}")
        summary.append(f"Successfully trained: {len(results['successful'])}")
        summary.append(f"Failed: {len(results['failed'])}")
        
        # Avoid division by zero
        if results['total'] > 0:
            success_rate = (len(results['successful']) / results['total'] * 100)
            summary.append(f"Success rate: {success_rate:.1f}%")
        else:
            summary.append(f"Success rate: N/A (no stocks attempted)")
        summary.append("")
        
        if results['successful']:
            summary.append("Top 10 models by R² score:")
            sorted_models = sorted(results['successful'], 
                                 key=lambda x: x['r2_score'], 
                                 reverse=True)
            
            for i, model in enumerate(sorted_models[:10], 1):
                summary.append(f"{i:2d}. {model['symbol']:12s} - R²: {model['r2_score']:.4f}, "
                             f"Data: {model['data_points']} days")
        
        if results['failed']:
            summary.append("")
            summary.append(f"Failed stocks ({len(results['failed'])}):")
            summary.append(", ".join(results['failed'][:20]))
            if len(results['failed']) > 20:
                summary.append(f"... and {len(results['failed'])-20} more")
        
        # Save summary
        summary_file = self.output_dir / "indian_stocks_training_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary))
        
        # Print to console
        print()
        print('\n'.join(summary))
        print()
        logging.info(f"📊 Summary saved: {summary_file}")


if __name__ == "__main__":
    print("=" * 70)
    print("INDIAN STOCK MODEL TRAINER")
    print("Train LSTM models on NSE stocks")
    print("=" * 70)
    print()
    
    # Check if data file exists
    data_file = "nse_data/nse_stock_data_2020_2024.parquet"
    
    if not os.path.exists(data_file):
        # Try CSV
        data_file = "nse_data/nse_stock_data_2020_2024.csv"
        if not os.path.exists(data_file):
            print("❌ Error: NSE data file not found!")
            print()
            print("Please run nse_data_downloader.py first to download the data:")
            print("   python nse_data_downloader.py")
            print()
            exit(1)
    
    print(f"📁 Data file: {data_file}")
    print(f"💾 Models will be saved to: models/pretrained/")
    print()
    print("⚙️  Training Configuration:")
    print("   • Top 100 stocks by trading volume")
    print("   • Minimum 200 days of data required")
    print("   • 60-day sequence length")
    print("   • 10 epochs per stock")
    print()
    print("⏱️  Estimated time: 30-60 minutes")
    print("💽 Storage required: ~500 MB")
    print()
    
    response = input("Start training? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print()
        print("🚀 Starting training...")
        print()
        
        try:
            # Initialize trainer
            trainer = IndianStockTrainer(data_file)
            
            # Train models
            results = trainer.train_all_stocks(
                top_n=100,  # Train top 100 stocks
                min_data_points=200  # Require at least 200 days of data
            )
            
            # Check if training was successful
            if results['total'] == 0:
                print()
                print("=" * 70)
                print("❌ TRAINING FAILED!")
                print("=" * 70)
                print()
                print("No stocks were trained. Possible reasons:")
                print("1. Dataset is empty (0 records)")
                print("2. No stocks found in the data")
                print("3. Data loading error")
                print()
                print("Please check:")
                print("   • nse_data/nse_stock_data_2020_2024.parquet exists")
                print("   • File is not empty (should be ~500 MB)")
                print("   • models/pretrained/training.log for details")
                exit(1)
            
            if len(results['successful']) == 0:
                print()
                print("=" * 70)
                print("⚠️  TRAINING COMPLETED WITH WARNINGS")
                print("=" * 70)
                print()
                print(f"Total stocks attempted: {results['total']}")
                print(f"❌ All {len(results['failed'])} stocks failed to train")
                print()
                print("Common reasons:")
                print("1. Not enough data points (need 200+ days)")
                print("2. Missing CLOSE price data")
                print("3. Data quality issues")
                print()
                print("Check models/pretrained/training.log for details")
                exit(1)
            
            print()
            print("=" * 70)
            print("🎉 TRAINING COMPLETED!")
            print("=" * 70)
            print()
            print(f"✅ Successfully trained: {len(results['successful'])} models")
            print(f"❌ Failed: {len(results['failed'])} stocks")
            
            if results['total'] > 0:
                success_rate = (len(results['successful']) / results['total'] * 100)
                print(f"📊 Success rate: {success_rate:.1f}%")
            
            print()
            print("📁 Models saved in: models/pretrained/")
            print()
            print("🚀 You can now use these models for fast predictions:")
            print("   GET /api/ai/predict/lstm-pretrained?symbol=RELIANCE&future_days=30")
            print()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Training interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Training cancelled")
