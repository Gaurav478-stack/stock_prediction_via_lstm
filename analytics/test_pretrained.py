"""
Test script for pre-trained models
"""
from services.lstm_prediction import run_lstm_prediction_pretrained
import time

# Test multiple stocks
test_symbols = ['TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']

print("=" * 80)
print("TESTING PRE-TRAINED LSTM MODELS")
print("=" * 80)
print()

results = []
for symbol in test_symbols:
    print(f"Testing {symbol}...")
    start_time = time.time()
    
    result = run_lstm_prediction_pretrained(symbol, future_days=30)
    elapsed = time.time() - start_time
    
    if result['success']:
        current = result.get('current_price', 0)
        predicted = result.get('predicted_price', 0)
        change = result.get('price_change_percent', 0)
        pretrained = result.get('using_pretrained', False)
        
        results.append({
            'symbol': symbol,
            'current': current,
            'predicted': predicted,
            'change': change,
            'time': elapsed,
            'pretrained': pretrained
        })
        
        print(f"  ✅ Success!")
        print(f"  Current Price: ${current:.2f}")
        print(f"  Predicted (30d): ${predicted:.2f}")
        print(f"  Change: {change:+.2f}%")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Using Pretrained: {pretrained}")
    else:
        print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
        results.append({
            'symbol': symbol,
            'error': result.get('error', 'Unknown error'),
            'time': elapsed
        })
    
    print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
successful = [r for r in results if 'error' not in r]
failed = [r for r in results if 'error' in r]

print(f"Total Tests: {len(results)}")
print(f"Successful: {len(successful)}")
print(f"Failed: {len(failed)}")
print()

if successful:
    avg_time = sum(r['time'] for r in successful) / len(successful)
    print(f"Average Prediction Time: {avg_time:.2f}s")
    print()
    
    print("Predictions:")
    for r in successful:
        trend = "📈" if r['change'] > 0 else "📉"
        print(f"  {r['symbol']:6} ${r['current']:8.2f} → ${r['predicted']:8.2f} ({r['change']:+6.2f}%) {trend}")

if failed:
    print()
    print("Failed:")
    for r in failed:
        print(f"  {r['symbol']}: {r.get('error', 'Unknown error')}")

print()
print("=" * 80)
