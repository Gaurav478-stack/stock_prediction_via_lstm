# Indian Stock Search Enhancement Guide

## Overview
The StockSense analytics service now includes enhanced support for searching and fetching Indian stocks using **company names** instead of just stock symbols.

## New Features

### 1. **Company Name Search**
You can now search for Indian stocks using:
- Full company names: "Reliance Industries", "Tata Consultancy Services"
- Short names: "Reliance", "TCS", "HDFC"
- Common abbreviations: "RIL", "HUL", "SBI"

### 2. **Supported Companies**
The system includes a comprehensive mapping of 80+ Indian companies:

#### Large Cap
- Reliance Industries (RELIANCE)
- Tata Consultancy Services (TCS)
- HDFC Bank (HDFCBANK)
- ICICI Bank (ICICIBANK)
- State Bank of India (SBIN)
- Infosys (INFY)
- Hindustan Unilever (HINDUNILVR)
- ITC (ITC)
- Bharti Airtel (BHARTIARTL)
- Kotak Mahindra Bank (KOTAKBANK)
- Larsen & Toubro (LT)
- Axis Bank (AXISBANK)
- Bajaj Finance (BAJFINANCE)

#### Tech Companies
- Wipro (WIPRO)
- Tech Mahindra (TECHM)
- HCL Technologies (HCLTECH)
- LTIMindtree (LTIM)
- Persistent Systems (PERSISTENT)
- Mphasis (MPHASIS)

#### Auto Sector
- Tata Motors (TATAMOTORS)
- Maruti Suzuki (MARUTI)
- Mahindra & Mahindra (M&M)
- Bajaj Auto (BAJAJ-AUTO)
- Hero MotoCorp (HEROMOTOCO)
- Eicher Motors (EICHERMOT)
- Tata Steel (TATASTEEL)

#### Pharma
- Sun Pharmaceutical (SUNPHARMA)
- Dr. Reddy's Laboratories (DRREDDY)
- Cipla (CIPLA)
- Divi's Laboratories (DIVISLAB)
- Apollo Hospitals (APOLLOHOSP)

#### FMCG
- Nestle India (NESTLEIND)
- Britannia Industries (BRITANNIA)
- Godrej Consumer (GODREJCP)
- Dabur (DABUR)
- Marico (MARICO)
- Tata Consumer (TATACONSUM)

#### Energy & Power
- ONGC (ONGC)
- NTPC (NTPC)
- Power Grid (POWERGRID)
- BPCL (BPCL)
- Coal India (COALINDIA)
- Adani Green (ADANIGREEN)

#### Cement & Materials
- Asian Paints (ASIANPAINT)
- Titan Company (TITAN)
- UltraTech Cement (ULTRACEMCO)
- Shree Cement (SHREECEM)
- Grasim Industries (GRASIM)

#### Adani Group
- Adani Enterprises (ADANIENT)
- Adani Ports (ADANIPORTS)

#### Insurance & Finance
- HDFC Life (HDFCLIFE)
- SBI Life (SBILIFE)
- Bajaj Finserv (BAJAJFINSV)
- IndusInd Bank (INDUSINDBK)

#### Metals & Mining
- JSW Steel (JSWSTEEL)
- Hindalco (HINDALCO)
- Vedanta (VEDL)

#### New Age Tech
- Zomato (ZOMATO)
- Paytm (PAYTM)
- Nykaa (NYKAA)
- PolicyBazaar (POLICYBZR)
- IRCTC (IRCTC)

#### Defense & PSU
- HAL - Hindustan Aeronautics (HAL)
- BEL - Bharat Electronics (BEL)

#### Others
- Pidilite (PIDILITIND)

## How It Works

### Architecture
```
StockDataService
    └── IndianStockService
            ├── Company Name Mapping (80+ companies)
            ├── Symbol Lookup with Fuzzy Matching
            ├── Real-time Data via yfinance
            └── Historical Data with NSE/BSE support
```

### Search Flow
1. User enters a search query (e.g., "reliance", "hdfc bank", "tcs")
2. System checks the Indian stock service first
3. Fuzzy matching finds the company even with partial names
4. Returns stock symbol with NSE (.NS) suffix
5. Fetches real-time or historical data

### API Usage

#### Search Symbols
```javascript
// Search for "reliance"
GET /stocks/search?query=reliance

Response:
[
  {
    "company_name": "Reliance Industries",
    "symbol": "RELIANCE",
    "nse_symbol": "RELIANCE.NS",
    "market": "India (NSE)"
  }
]
```

#### Get Quote by Company Name
```javascript
// Get quote for "hdfc bank"
GET /stocks/quote/hdfc bank

Response:
{
  "symbol": "HDFCBANK",
  "name": "HDFC Bank Ltd.",
  "price": 1645.30,
  "current_price": 1645.30,
  "open": 1650.00,
  "high": 1655.00,
  "low": 1640.00,
  "volume": 5234567,
  "change": -4.70,
  "changePercent": -0.28,
  "previous_close": 1650.00,
  "currency": "INR",
  "market_cap": 1234567890000,
  "timestamp": "2024-01-15T10:30:00",
  "source": "Yahoo Finance"
}
```

#### Get Historical Data
```javascript
// Get historical data for "tcs"
GET /stocks/history/tcs?period=1mo&interval=1d

Response:
{
  "symbol": "TCS",
  "dates": ["2024-01-01", "2024-01-02", ...],
  "open": [3850.00, 3860.00, ...],
  "high": [3870.00, 3880.00, ...],
  "low": [3840.00, 3850.00, ...],
  "close": [3865.00, 3875.00, ...],
  "volume": [1234567, 2345678, ...],
  "timestamp": "2024-01-15T10:30:00",
  "source": "Yahoo Finance"
}
```

## Fuzzy Matching Examples

The system supports intelligent fuzzy matching:

| User Input | Matches |
|------------|---------|
| "reliance" | Reliance Industries (RELIANCE) |
| "ril" | Reliance Industries (RELIANCE) |
| "hdfc" | HDFC Bank (HDFCBANK) |
| "hdfc bank" | HDFC Bank (HDFCBANK) |
| "tata" | Multiple Tata companies (TCS, TATAMOTORS, TATASTEEL, etc.) |
| "airtel" | Bharti Airtel (BHARTIARTL) |
| "sbi" | State Bank of India (SBIN) |
| "sun pharma" | Sun Pharmaceutical (SUNPHARMA) |

## Frontend Integration

### Dashboard Search
Users can now search for Indian stocks using:
1. Stock symbols (e.g., "RELIANCE.NS")
2. Company names (e.g., "Reliance Industries")
3. Short names (e.g., "Reliance", "RIL")

The search results will automatically show:
- Company name
- Stock symbol (without .NS suffix)
- NSE symbol (with .NS suffix)
- Market indicator (India NSE)

### Example Usage in Frontend
```javascript
// Search for Indian stocks
const searchResults = await fetch('/stocks/search?query=hdfc');
const data = await searchResults.json();

// Get real-time quote
const quote = await fetch('/stocks/quote/hdfc bank');
const quoteData = await quote.json();

// Display stock data
console.log(`${quoteData.name}: ₹${quoteData.price}`);
```

## Benefits

1. **User-Friendly**: No need to remember exact stock symbols
2. **Comprehensive**: Covers 80+ major Indian companies
3. **Flexible**: Supports multiple name variations for each company
4. **Fast**: Real-time data from Yahoo Finance
5. **Reliable**: Automatic fallback to standard yfinance for edge cases

## Technical Details

### Files Modified
- `analytics/services/stock_data.py` - Enhanced with Indian stock support
- `analytics/services/indian_stock_service.py` - New service for Indian stocks

### Dependencies
- yfinance 0.2.18 (already installed)
- Python 3.13.9 (already installed)

### No Additional Installation Required
All necessary libraries are already included in your current setup.

## Testing

You can test the new functionality immediately:

### Test 1: Search by Company Name
```bash
curl http://localhost:8000/stocks/search?query=reliance
```

### Test 2: Get Quote by Name
```bash
curl http://localhost:8000/stocks/quote/hdfc%20bank
```

### Test 3: Get Historical Data
```bash
curl http://localhost:8000/stocks/history/tcs?period=1mo
```

## Future Enhancements (Optional)

If you want to add more features in the future:
1. **Alpha Vantage Integration**: For more detailed financial data
2. **NSEPy Integration**: For NSE-specific data and analytics
3. **Real-time WebSocket**: For live price updates
4. **Technical Indicators**: RSI, MACD, Moving Averages, etc.
5. **Fundamental Data**: P/E ratio, Market Cap, Dividend Yield, etc.

## Support

For any issues or questions:
1. Check server logs at http://localhost:8000
2. Verify symbol mapping in `indian_stock_service.py`
3. Test with simple queries first (e.g., "reliance", "tcs")
4. Ensure yfinance is returning data for .NS symbols
