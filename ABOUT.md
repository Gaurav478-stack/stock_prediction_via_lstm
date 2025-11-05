# StockSense - AI-Powered Stock Analysis Platform

A comprehensive stock market analysis platform with AI-powered predictions, portfolio optimization, and real-time market insights for both Indian (NSE) and US markets.

## 🚀 Features

- **AI-Powered Stock Predictions**: LSTM-based models for price forecasting
- **Multi-Market Support**: Analyze stocks from NSE (Indian) and US markets
- **Portfolio Optimization**: Smart portfolio allocation using Modern Portfolio Theory
- **Technical Analysis**: Multiple technical indicators and chart patterns
- **Sentiment Analysis**: News-based sentiment scoring
- **Risk Analysis**: Value at Risk (VaR) and risk metrics
- **Real-time Data**: Live stock quotes and historical data
- **Interactive Visualizations**: Beautiful charts and dashboards

## 📦 Tech Stack

### Frontend
- HTML5, CSS3, JavaScript
- Chart.js for visualizations
- Responsive design

### Backend
- Node.js & Express
- MongoDB
- JWT Authentication

### Analytics Engine
- Python 3.8+
- TensorFlow/Keras for LSTM models
- Pandas, NumPy for data processing
- yfinance for stock data

## 🛠️ Local Development Setup

### Prerequisites
- Node.js (v14+)
- Python 3.8+
- MongoDB
- Git

### Backend Setup
```bash
cd backend
npm install
# Create .env file with your configurations
npm start
```

### Analytics Setup
```bash
cd analytics
pip install -r requirements.txt
python app.py
```

### Frontend
Simply open `frontend/index.html` in a browser or serve it with a local server.

## 🌐 Deployment

### Frontend - GitHub Pages

1. Push code to GitHub
2. Go to repository Settings → Pages
3. Set source to main branch / root
4. Your site will be live at `https://yourusername.github.io/stocksense`

### Backend - Render

1. Create account on [Render.com](https://render.com)
2. Create new Web Service
3. Connect your GitHub repository
4. Set build command: `cd backend && npm install`
5. Set start command: `cd backend && npm start`
6. Add environment variables
7. Deploy

### Analytics - Render

1. Create new Web Service on Render
2. Set build command: `cd analytics && pip install -r requirements.txt`
3. Set start command: `cd analytics && python app.py`
4. Add environment variables
5. Deploy

## 🔐 Environment Variables

### Backend (.env)
```
MONGODB_URI=your_mongodb_uri
JWT_SECRET=your_jwt_secret
ALPHA_VANTAGE_API_KEY=your_api_key
PORT=5000
```

### Analytics
```
FLASK_ENV=production
PORT=8000
```

## 📖 Documentation

- [Algorithm Explanation](ALGORITHM_EXPLAINED.md)
- [Features Analysis](FEATURES_ANALYSIS.md)
- [Indian Stocks Guide](INDIAN_STOCKS_GUIDE.md)
- [Security Documentation](SECURITY.md)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 👤 Author

Your Name
- GitHub: [@yourusername](https://github.com/yourusername)

## 🙏 Acknowledgments

- Alpha Vantage for stock data API
- NSE India for Indian stock data
- TensorFlow team for the amazing ML framework
