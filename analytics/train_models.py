"""
Standalone Training Script
Run this to pre-train models on all stocks

Usage:
    python train_models.py
    python train_models.py --period 2y --epochs 15
"""

import sys
import argparse
from services.model_trainer import run_full_training_pipeline


def main():
    parser = argparse.ArgumentParser(description='Train LSTM models on all stocks')
    parser.add_argument('--period', type=str, default='1y', 
                       choices=['1y', '2y', '5y'],
                       help='Historical data period (default: 1y)')
    parser.add_argument('--epochs', type=int, default=10,
                       help='Training epochs per stock (default: 10)')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          STOCKSENSE MODEL TRAINING PIPELINE                  ║
╚══════════════════════════════════════════════════════════════╝

Configuration:
  📅 Period:  {args.period}
  🔄 Epochs:  {args.epochs}
  📊 Stocks:  500+ (Indian + US markets)

This will:
  1. Download 200+ Indian stocks
  2. Train models for Indian stocks
  3. Download 300+ US stocks
  4. Train models for US stocks
  5. Save all models and metadata

⏱️  Estimated time: 30-60 minutes
💾 Storage required: ~2-3 GB

Press Ctrl+C to cancel...
""")
    
    try:
        result = run_full_training_pipeline(period=args.period, epochs=args.epochs)
        
        if result['success']:
            print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  ✅ TRAINING COMPLETED!                      ║
╚══════════════════════════════════════════════════════════════╝

📊 Results:
  • Total models: {result['total_models']}
  • Indian stocks: {result['indian_summary']['successful']}
  • US stocks: {result['us_summary']['successful']}
  
📁 Models saved in: models/pretrained/

🚀 You can now use fast predictions with:
   GET /api/ai/predict/lstm-pretrained?symbol=AAPL&future_days=30
""")
            return 0
        else:
            print(f"\n❌ Training failed: {result.get('error')}")
            return 1
            
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
