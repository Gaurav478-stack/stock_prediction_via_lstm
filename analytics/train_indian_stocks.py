"""
Train Indian Stocks Only
Run this to train only Indian stocks with fixed data validation
"""

import sys
from services.model_trainer import ModelTrainer
from services.stock_data_fetcher import download_all_indian_stocks

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║        INDIAN STOCKS TRAINING (WITH DATA VALIDATION)         ║
╚══════════════════════════════════════════════════════════════╝

Configuration:
  📅 Period:  1y
  🔄 Epochs:  10
  📊 Stocks:  200+ Indian stocks
  🛡️  Enhanced data validation for infinity/NaN handling

This will:
  1. Download 200+ Indian stocks
  2. Clean and validate data
  3. Train models with edge case handling
  4. Save all models and metadata

⏱️  Estimated time: 15-20 minutes

Press Ctrl+C to cancel...
""")
    
    try:
        # Download Indian stocks
        print("📥 Downloading Indian stocks...")
        indian_data = download_all_indian_stocks(period="1y")
        print(f"✅ Downloaded {len(indian_data)} Indian stocks")
        
        # Train models
        print("\n🔥 Training Indian stocks with data validation...")
        trainer = ModelTrainer()
        summary = trainer.train_all_stocks(indian_data, "Indian", epochs=10)
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              ✅ INDIAN TRAINING COMPLETED!                   ║
╚══════════════════════════════════════════════════════════════╝

📊 Results:
  • Total downloaded: {len(indian_data)}
  • Successfully trained: {summary['successful']}
  • Failed: {summary['failed']}
  • Success rate: {summary['successful']/len(indian_data)*100:.1f}%

📁 Models saved in: models/pretrained/

🚀 You can now use fast predictions with Indian stocks:
   GET /api/ai/predict/lstm-pretrained?symbol=RELIANCE.NS&future_days=30
""")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
