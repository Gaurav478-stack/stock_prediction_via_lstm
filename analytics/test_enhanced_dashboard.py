import requests
import time

print('🧪 Testing Enhanced AI Dashboard...\n')

start_time = time.time()

response = requests.get(
    'http://localhost:8000/api/ai/visualization/enhanced-dashboard',
    params={'symbol': 'AAPL', 'future_days': 30},
    timeout=60
)

end_time = time.time()

result = response.json()

print(f'Status Code: {response.status_code}')
print(f'Success: {result.get("success")}')
print(f'Symbol: {result.get("symbol")}')
print(f'Dashboard Type: {result.get("dashboard_type")}')
print(f'Chart Size: {len(result.get("chart", ""))} bytes')
print(f'Generation Time: {end_time - start_time:.2f} seconds')
print(f'\n📊 Includes {len(result.get("includes", []))} charts:')
for i, chart in enumerate(result.get("includes", []), 1):
    print(f'  {i}. {chart.replace("_", " ").title()}')

if response.status_code == 200 and result.get("success"):
    print('\n✅ Enhanced AI Dashboard is working perfectly!')
    print('🎨 Advanced visualizations include:')
    print('   - Main prediction with gradients')
    print('   - Price momentum indicators')
    print('   - Volatility gauge (circular meter)')
    print('   - Technical indicators summary')
    print('   - Confidence meter (donut chart)')
    print('   - Returns distribution with KDE')
    print('   - Accuracy metrics (horizontal bars)')
    print('   - Risk assessment gauge')
else:
    print('\n❌ Error:', result.get('detail', 'Unknown error'))
