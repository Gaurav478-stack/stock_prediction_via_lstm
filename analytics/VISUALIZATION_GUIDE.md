# 📊 Stock Prediction Visualization Guide

## Overview
StockSense now includes **Python-based matplotlib visualization** for stock predictions, generating beautiful, publication-ready charts with professional styling.

---

## 🎨 Features

### 1. **Prediction Timeline Chart**
Beautiful single-chart visualization showing:
- **Historical Price Data** (blue line with filled area)
- **30-Day Future Predictions** (purple dashed line with squares)
- **Confidence Bands** (±5% shaded area)
- **Current Price Annotation** (blue box with arrow)
- **Predicted Price Annotation** (green/red box with % change)
- **Prediction Start Line** (red vertical dashed line)

### 2. **Comprehensive Analysis**
Multi-chart dashboard with 6 subplots:
1. **Main Price Prediction** - Timeline with historical + predicted
2. **Price Distribution** - Histogram comparison of historical vs predicted
3. **Daily Returns** - Return percentage analysis
4. **Rolling Volatility** - 7-day and 30-day volatility trends
5. **Model Performance Metrics** - Bar chart (MAE, RMSE, MAPE, R²)

---

## 🚀 API Endpoints

### 1. Get Prediction with Optional Visualization
```http
GET /api/ai/predict/lstm-pretrained?symbol=AAPL&future_days=30&include_visualization=true
```

**Parameters:**
- `symbol` (required): Stock symbol or company name
- `future_days` (optional): Days to predict (1-90, default: 30)
- `include_visualization` (optional): Include chart (default: false)

**Response:**
```json
{
  "success": true,
  "symbol": "AAPL",
  "resolved_symbol": "AAPL",
  "current_price": 269.05,
  "predicted_price": 257.28,
  "price_change_percent": -4.37,
  "predictions": [269.05, 268.12, ...],
  "future_dates": ["2025-01-22", "2025-01-23", ...],
  "historical_prices": [245.32, 247.18, ...],
  "historical_dates": ["2024-07-22", "2024-07-23", ...],
  "visualization": "iVBORw0KGgoAAAANSUhEUg..." // base64 PNG
}
```

### 2. Get Prediction Chart Only
```http
GET /api/ai/visualization/prediction-chart?symbol=AAPL&future_days=30
```

**Response:**
```json
{
  "success": true,
  "symbol": "AAPL",
  "chart": "iVBORw0KGgoAAAANSUhEUg...",
  "format": "base64_png"
}
```

### 3. Get Comprehensive Analysis
```http
GET /api/ai/visualization/comprehensive-analysis?symbol=NVDA&future_days=30
```

**Response:**
```json
{
  "success": true,
  "symbol": "NVDA",
  "chart": "iVBORw0KGgoAAAANSUhEUg...",
  "format": "base64_png",
  "includes": [
    "price_prediction",
    "distribution",
    "returns",
    "volatility",
    "metrics"
  ]
}
```

---

## 💻 Usage Examples

### Python Client
```python
import requests
import base64
from PIL import Image
from io import BytesIO

# Get prediction with visualization
response = requests.get('http://localhost:8000/api/ai/predict/lstm-pretrained', 
                       params={'symbol': 'AAPL', 
                              'future_days': 30, 
                              'include_visualization': True})
data = response.json()

# Display chart
if 'visualization' in data:
    chart_data = base64.b64decode(data['visualization'])
    img = Image.open(BytesIO(chart_data))
    img.show()
    
# Or save to file
with open('AAPL_prediction.png', 'wb') as f:
    f.write(chart_data)
```

### JavaScript/HTML
```html
<img id="chart" alt="Stock Prediction">

<script>
async function loadChart(symbol) {
    const response = await fetch(
        `http://localhost:8000/api/ai/visualization/prediction-chart?symbol=${symbol}&future_days=30`
    );
    const data = await response.json();
    
    if (data.success) {
        document.getElementById('chart').src = 
            `data:image/png;base64,${data.chart}`;
    }
}

loadChart('AAPL');
</script>
```

### cURL
```bash
# Get prediction chart
curl "http://localhost:8000/api/ai/visualization/prediction-chart?symbol=AAPL&future_days=30" \
  | jq -r '.chart' \
  | base64 -d > AAPL_chart.png

# Get comprehensive analysis
curl "http://localhost:8000/api/ai/visualization/comprehensive-analysis?symbol=NVDA&future_days=30" \
  | jq -r '.chart' \
  | base64 -d > NVDA_analysis.png
```

---

## 🎯 Test Page

Open `test_visualization.html` in your browser to test the visualization system interactively:

```bash
# Make sure server is running
cd analytics
python main.py

# Open test page in browser
start test_visualization.html
```

**Features:**
- ✅ Test both chart types
- ✅ Real-time generation
- ✅ View prediction statistics
- ✅ Beautiful gradient UI
- ✅ Error handling

---

## 🎨 Chart Styling

### Colors
- **Historical Data**: `#3B82F6` (Blue)
- **Predictions**: `#A855F7` (Purple)
- **Positive Change**: `#10B981` (Green)
- **Negative Change**: `#EF4444` (Red)
- **Prediction Start**: `#EF4444` (Red dashed)
- **Confidence Band**: `#A855F7` (Purple transparent)

### Fonts
- **Title**: 16pt Bold
- **Axis Labels**: 13pt Bold
- **Annotations**: 11pt Bold
- **Legend**: 11pt Regular

### Layout
- **DPI**: 100 (web) / 150 (print)
- **Figure Size**: 16x9 inches (prediction), 18x12 inches (comprehensive)
- **Grid**: Seaborn darkgrid theme
- **Transparency**: Smart alpha blending

---

## 📦 Dependencies

```python
matplotlib >= 3.8.0
seaborn >= 0.13.0
numpy >= 1.24.0
pandas >= 2.0.0
```

Install with:
```bash
pip install matplotlib>=3.8.0 seaborn>=0.13.0
```

---

## 🔧 Configuration

### Output Formats

**Base64 (Web)**
```python
from services.prediction_visualizer import generate_prediction_visualization

chart_base64 = generate_prediction_visualization(
    prediction_result, 
    output_format='base64'
)
```

**File (Local)**
```python
chart_path = generate_prediction_visualization(
    prediction_result, 
    output_format='file'
)
# Saved to: visualizations/AAPL_prediction_20250122_143052.png
```

---

## 📊 Chart Types

### 1. Prediction Chart
**Purpose:** Quick visual of price forecast  
**Size:** ~300KB base64  
**Generation Time:** 2-3 seconds  
**Best For:** Web display, dashboards, quick analysis

### 2. Comprehensive Analysis
**Purpose:** Deep dive with multiple metrics  
**Size:** ~320KB base64  
**Generation Time:** 3-4 seconds  
**Best For:** Reports, detailed analysis, presentations

---

## 🚨 Error Handling

### Common Errors

**1. No Data Available**
```json
{
  "detail": "Chart generation error: No data found for INVALID"
}
```

**2. Invalid Symbol**
```json
{
  "detail": "Prediction failed: Symbol not found"
}
```

**3. Visualization Error**
```json
{
  "success": true,
  "visualization_error": "Chart generation failed: ..."
}
```
*Note: Prediction still returns even if visualization fails*

---

## 🎯 Performance

### Benchmarks (AAPL, 30 days)
- **Prediction Only**: 2.35s
- **Prediction + Chart**: 4.82s
- **Chart Only**: 2.47s
- **Comprehensive**: 3.15s

### Optimization Tips
1. **Cache predictions** - Reuse data for multiple charts
2. **Async generation** - Generate charts in background
3. **Lazy loading** - Load charts on demand
4. **CDN storage** - Upload generated charts to S3/CDN

---

## 📝 Code Structure

### Service Files
```
services/
├── prediction_visualizer.py    # Main visualization service
├── lstm_prediction.py          # Prediction data source
└── company_search.py           # Symbol resolution
```

### Key Classes
```python
class PredictionVisualizer:
    - create_prediction_chart()      # Single timeline chart
    - create_comparison_chart()      # 6-subplot analysis
    - _setup_style()                 # Theme configuration
    - _save_or_encode()             # Output handling
```

### Helper Functions
```python
generate_prediction_visualization()      # Wrapper for quick chart
generate_comprehensive_analysis()        # Wrapper for analysis
```

---

## 🔮 Future Enhancements

### Planned Features
- [ ] **Interactive Charts** (plotly.js)
- [ ] **Custom Date Ranges** (flexible prediction periods)
- [ ] **Comparison Charts** (multiple stocks)
- [ ] **Export Options** (PDF, SVG, HTML)
- [ ] **Real-time Updates** (WebSocket streaming)
- [ ] **Custom Styling** (user themes)
- [ ] **Technical Indicators** (RSI, MACD, Bollinger Bands)
- [ ] **Download Button** (frontend integration)

---

## 📚 Examples

### Multiple Stocks
```python
stocks = ['AAPL', 'NVDA', 'TSLA', 'MSFT']
for symbol in stocks:
    response = requests.get(
        'http://localhost:8000/api/ai/visualization/prediction-chart',
        params={'symbol': symbol, 'future_days': 30}
    )
    data = response.json()
    with open(f'{symbol}_chart.png', 'wb') as f:
        f.write(base64.b64decode(data['chart']))
```

### Batch Analysis
```python
import concurrent.futures

def generate_chart(symbol):
    response = requests.get(
        'http://localhost:8000/api/ai/visualization/comprehensive-analysis',
        params={'symbol': symbol}
    )
    return response.json()

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(generate_chart, stocks))
```

---

## ✅ Testing

### Test Visualization Service
```bash
cd analytics/services
python prediction_visualizer.py
```

### Test API Endpoints
```bash
# Test prediction chart
curl "http://localhost:8000/api/ai/visualization/prediction-chart?symbol=AAPL&future_days=30" > response.json

# Test comprehensive analysis  
curl "http://localhost:8000/api/ai/visualization/comprehensive-analysis?symbol=NVDA&future_days=30" > analysis.json
```

### Test HTML Interface
```bash
start test_visualization.html
# Or
python -m http.server 8080
# Then open http://localhost:8080/test_visualization.html
```

---

## 📖 Documentation

### Related Guides
- [LSTM Prediction Guide](COMPLETE_STOCK_DATABASE_GUIDE.md)
- [Company Search Guide](COMPANY_SEARCH_GUIDE.md)
- [Animation Guide](ANIMATION_GUIDE.md)
- [Test Results](TEST_RESULTS.md)

---

## 🎉 Summary

✅ **3 New API Endpoints** for visualization  
✅ **2 Chart Types** (prediction + comprehensive)  
✅ **Base64 Encoding** for web delivery  
✅ **Beautiful Styling** with matplotlib/seaborn  
✅ **Fast Generation** (2-4 seconds)  
✅ **Test Interface** with live preview  
✅ **Company Name Support** (case-insensitive)  
✅ **Error Handling** with graceful fallbacks

**Now you can visualize stock predictions with publication-quality charts! 📊🚀**
