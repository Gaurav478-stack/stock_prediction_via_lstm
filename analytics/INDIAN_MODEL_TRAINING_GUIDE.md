# Indian Stock Model Training Guide

This guide explains how to download NSE (National Stock Exchange) data and train LSTM models on Indian stocks.

## 📋 Overview

The process consists of two main steps:

1. **Download NSE Data** - Downloads 5 years of historical bhavcopy data (2020-2024)
2. **Train Models** - Trains LSTM models on top 100 Indian stocks

## 🚀 Quick Start

### Step 1: Download NSE Data

```bash
cd "c:\Users\Gaura\OneDrive\Desktop\dav intial stage\stocksense\analytics"
python nse_data_downloader.py
```

**What it does:**
- Downloads daily bhavcopy data from NSE archives (2020-2024)
- Processes and cleans the data
- Saves as both Parquet and CSV formats
- Creates summary statistics

**Time required:** 2-4 hours
**Storage required:** ~500 MB - 1 GB
**Output files:**
- `nse_data/nse_stock_data_2020_2024.parquet` (main data)
- `nse_data/nse_stock_data_2020_2024.csv` (backup format)
- `nse_data/nse_stock_data_2020_2024_summary.txt` (statistics)

### Step 2: Train LSTM Models

```bash
python train_indian_models.py
```

**What it does:**
- Loads the downloaded NSE data
- Selects top 100 stocks by trading volume
- Trains LSTM model for each stock
- Saves models, scalers, and metadata

**Time required:** 30-60 minutes
**Storage required:** ~500 MB
**Output:**
- `models/pretrained/{SYMBOL}.keras` (trained models)
- `models/pretrained/{SYMBOL}_scaler.pkl` (price scalers)
- `models/pretrained/{SYMBOL}_metadata.pkl` (training stats)

## 📊 Data Details

### NSE Bhavcopy Data Structure

The downloaded data includes:
- **DATE** - Trading date
- **SYMBOL** - Stock symbol (e.g., RELIANCE, TCS, INFY)
- **OPEN** - Opening price
- **HIGH** - Highest price
- **LOW** - Lowest price
- **CLOSE** - Closing price
- **VOLUME** - Trading volume
- **SERIES** - Security series (EQ, BE)

### Model Training Configuration

```python
sequence_length = 60     # 60 days of historical data
lstm_units = 50          # LSTM layer size
epochs = 10              # Training epochs
batch_size = 32          # Batch size
min_data_points = 200    # Minimum 200 days required
top_n = 100              # Train top 100 stocks
```

## 📈 Top Indian Stocks Included

The training typically includes major stocks like:

**IT Sector:**
- TCS, INFY (Infosys), WIPRO, HCLTECH, TECHM

**Banking & Finance:**
- HDFC, HDFCBANK, ICICIBANK, SBIN, AXISBANK, KOTAKBANK

**Energy:**
- RELIANCE, ONGC, NTPC, POWERGRID

**Auto:**
- TATAMOTORS, MARUTI, M&M, BAJAJ-AUTO

**FMCG:**
- ITC, HINDUNILVR, NESTLEIND, BRITANNIA

**Pharma:**
- SUNPHARMA, DRREDDY, CIPLA, DIVISLAB

And many more based on trading volume!

## 🔧 Troubleshooting

### Download Issues

**Problem:** "No data for [date] (holiday)"
- **Solution:** This is normal! NSE doesn't trade on weekends/holidays.

**Problem:** "Connection timeout"
- **Solution:** The script has automatic retry. Just wait or restart.

**Problem:** "404 errors"
- **Solution:** Some dates may not have data. The script handles this automatically.

### Training Issues

**Problem:** "Not enough data" warnings
- **Solution:** Normal for stocks with limited trading history. They're skipped automatically.

**Problem:** "Out of memory"
- **Solution:** Reduce `top_n` parameter or `batch_size` in the script.

**Problem:** "Training very slow"
- **Solution:** Normal on CPU. Consider reducing `epochs` or training fewer stocks.

## 📁 File Structure

```
stocksense/analytics/
├── nse_data_downloader.py          # Script to download NSE data
├── train_indian_models.py          # Script to train models
├── nse_data/                        # Downloaded data folder
│   ├── nse_stock_data_2020_2024.parquet
│   ├── nse_stock_data_2020_2024.csv
│   ├── nse_stock_data_2020_2024_summary.txt
│   └── nse_downloader.log
└── models/pretrained/               # Trained models folder
    ├── RELIANCE.keras
    ├── RELIANCE_scaler.pkl
    ├── RELIANCE_metadata.pkl
    ├── TCS.keras
    ├── TCS_scaler.pkl
    ├── TCS_metadata.pkl
    └── ... (more stocks)
```

## 🎯 Usage After Training

Once models are trained, you can use them via the API:

```bash
# Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Make prediction request
GET http://localhost:8000/api/ai/predict/lstm-pretrained?symbol=RELIANCE&future_days=30
```

The frontend will automatically use these pre-trained models for instant predictions!

## ⚙️ Customization

### Change Date Range

Edit `nse_data_downloader.py`:

```python
start_date = datetime(2020, 1, 1)  # Change start year
end_date = datetime(2024, 12, 31)  # Change end year
```

### Train More/Fewer Stocks

Edit `train_indian_models.py`:

```python
results = trainer.train_all_stocks(
    top_n=100,              # Change to 50, 200, etc.
    min_data_points=200     # Minimum days of data
)
```

### Adjust Model Parameters

Edit `train_indian_models.py` in `__init__` method:

```python
self.sequence_length = 60   # Days of historical data
self.lstm_units = 50        # LSTM complexity
self.epochs = 10            # Training duration
self.batch_size = 32        # Memory usage
```

## 📊 Performance Metrics

Models are evaluated using:
- **R² Score** - How well predictions fit actual data (higher is better)
- **MSE** - Mean Squared Error (lower is better)
- **Training Loss** - Final loss value

Check `models/pretrained/indian_stocks_training_summary.txt` for detailed results.

## 🎉 Benefits

✅ **Fast Predictions** - Pre-trained models give instant results
✅ **High Quality** - Trained on 5 years of real NSE data
✅ **100 Stocks** - Covers major Indian companies
✅ **Auto Updates** - Retrain periodically for latest patterns
✅ **Production Ready** - Optimized for real-time API usage

## 📝 Notes

1. **Internet Required** - For downloading NSE data
2. **Be Patient** - Initial download takes 2-4 hours
3. **One-Time Setup** - Only needs to run once (or periodically)
4. **Respectful** - Script includes delays to avoid overloading NSE servers
5. **Legal** - Uses publicly available NSE archive data

## 🔄 Updating Models

To update models with latest data:

1. Re-run the downloader with updated date range
2. Re-run the training script
3. Models will be overwritten with new versions

---

**Ready to start?**

```bash
# Step 1: Download data
python nse_data_downloader.py

# Step 2: Train models (after download completes)
python train_indian_models.py
```

Good luck! 🚀
