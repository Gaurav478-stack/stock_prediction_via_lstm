import requests

print('🧪 Testing Full Analysis Visualization...\n')

response = requests.get(
    'http://localhost:8000/api/ai/visualization/comprehensive-analysis',
    params={'symbol': 'AAPL', 'future_days': 30}
)

result = response.json()

print(f'Status Code: {response.status_code}')
print(f'Success: {result.get("success")}')
print(f'Symbol: {result.get("symbol")}')
print(f'Has Chart: {"chart" in result}')
print(f'Chart Size: {len(result.get("chart", ""))} bytes')
print(f'Includes: {result.get("includes")}')

if response.status_code == 200 and result.get("success"):
    print('\n✅ Full Analysis visualization is working perfectly!')
    print('📊 6-subplot analysis includes:')
    for item in result.get("includes", []):
        print(f'   - {item}')
else:
    print('\n❌ Error:', result.get('detail', 'Unknown error'))
