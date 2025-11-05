"""
Comprehensive Stock Data Fetcher for Indian and US Markets
Uses nsepy for Indian stocks and yfinance for US stocks
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date, timedelta
from tqdm import tqdm
import time

try:
    from nsepy import get_history
    NSEPY_AVAILABLE = True
except ImportError:
    NSEPY_AVAILABLE = False
    print("Warning: nsepy not available. Install with: pip install nsepy")


def calculate_technical_indicators(data):
    """
    Calculate technical indicators for the data with edge case handling
    
    Args:
        data: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added technical indicators
    """
    df = data.copy()
    
    # Ensure required columns exist
    if 'Close' not in df.columns:
        return df
    
    # Replace zeros with small value to avoid division by zero
    df['Close'] = df['Close'].replace(0, np.nan)
    df = df.dropna(subset=['Close'])
    
    if len(df) == 0:
        return df
    
    # Moving averages
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # Price momentum (with infinity handling)
    df['Price_Change'] = df['Close'].pct_change()
    df['Price_Change'] = df['Price_Change'].replace([np.inf, -np.inf], 0)
    
    # Price range (avoid division by zero)
    df['Price_Range'] = (df['High'] - df['Low']) / df['Close'].replace(0, np.nan)
    df['Price_Range'] = df['Price_Range'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Volume momentum (with infinity handling)
    if 'Volume' in df.columns:
        df['Volume'] = df['Volume'].replace(0, np.nan)
        df['Volume_Change'] = df['Volume'].pct_change()
        df['Volume_Change'] = df['Volume_Change'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # RSI (Relative Strength Index) with division by zero handling
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    # Avoid division by zero in RS calculation
    rs = gain / loss.replace(0, np.nan)
    rs = rs.replace([np.inf, -np.inf], 100).fillna(50)  # Default to neutral RSI
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].clip(0, 100)  # Ensure RSI is between 0-100
    
    # Final cleanup: replace any remaining infinity values
    df = df.replace([np.inf, -np.inf], np.nan)
    
    return df


def download_nse_data(symbol, start_date, end_date):
    """
    Download data directly from NSE using nsepy
    
    Args:
        symbol: NSE stock symbol (without .NS suffix)
        start_date: Start date
        end_date: End date
        
    Returns:
        DataFrame with stock data and technical indicators
    """
    if not NSEPY_AVAILABLE:
        return None
        
    try:
        # Remove .NS suffix if present
        if symbol.endswith('.NS'):
            symbol = symbol.replace('.NS', '')
        
        data = get_history(
            symbol=symbol,
            start=start_date,
            end=end_date,
            index=False
        )
        
        # Rename columns to match your model
        data = data.rename(columns={
            'Last': 'Close',
            'Turnover': 'Volume'
        })
        
        # Calculate technical indicators
        data = calculate_technical_indicators(data)
        return data.dropna()
        
    except Exception as e:
        print(f"Error downloading {symbol} from NSE: {e}")
        return None


def download_all_indian_stocks(period="1y"):
    """
    Download all actively traded Indian stocks (200+ stocks)
    
    Args:
        period: Period for historical data (default: 1y)
        
    Returns:
        Dictionary of ticker: DataFrame
    """
    # Comprehensive list of Indian stocks (200+ stocks)
    all_indian_stocks = [
        # Nifty 50
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
        "ICICIBANK.NS", "KOTAKBANK.NS", "BHARTIARTL.NS", "ITC.NS", "SBIN.NS",
        "BAJFINANCE.NS", "ASIANPAINT.NS", "HCLTECH.NS", "MARUTI.NS", "TITAN.NS",
        "SUNPHARMA.NS", "AXISBANK.NS", "ULTRACEMCO.NS", "M&M.NS", "TECHM.NS",
        "WIPRO.NS", "NESTLEIND.NS", "POWERGRID.NS", "NTPC.NS", "TATASTEEL.NS",
        "INDUSINDBK.NS", "BAJAJFINSV.NS", "DRREDDY.NS", "CIPLA.NS", "HDFCLIFE.NS",
        
        # Next 100 stocks
        "SBILIFE.NS", "ONGC.NS", "COALINDIA.NS", "GRASIM.NS", "JSWSTEEL.NS",
        "TATAMOTORS.NS", "ADANIPORTS.NS", "BPCL.NS", "HINDALCO.NS", "DIVISLAB.NS",
        "UPL.NS", "SHREECEM.NS", "APOLLOHOSP.NS", "EICHERMOT.NS", "BRITANNIA.NS",
        "HEROMOTOCO.NS", "LT.NS", "TATACONSUM.NS", "HINDZINC.NS", "ADANIENT.NS",
        
        # Mid-cap stocks
        "PIDILITIND.NS", "BIOCON.NS", "MOTHERSON.NS", "BERGEPAINT.NS", "HAVELLS.NS",
        "GODREJCP.NS", "DABUR.NS", "VOLTAS.NS", "AMBUJACEM.NS", "ACC.NS",
        "ICICIPRULI.NS", "SRF.NS", "MARICO.NS", "COLPAL.NS", "BAJAJHLDNG.NS",
        "TORNTPHARM.NS", "CADILAHC.NS", "LUPIN.NS", "AUROPHARMA.NS", "GLENMARK.NS",
        
        # Small-cap stocks
        "AARTIIND.NS", "ALKEM.NS", "BALKRISIND.NS", "BHEL.NS", "CANBK.NS",
        "FEDERALBNK.NS", "IDFCFIRSTB.NS", "IOB.NS", "JINDALSTEL.NS", "JSWENERGY.NS",
        "KAJARIACER.NS", "LICHSGFIN.NS", "MANAPPURAM.NS", "MFSL.NS", "NHPC.NS",
        "OIL.NS", "PEL.NS", "PNB.NS", "RBLBANK.NS", "SAIL.NS",
        
        # Additional sectors
        "ADANIGREEN.NS", "ADANIPOWER.NS", "ADANITRANS.NS", "ABCAPITAL.NS", "ABFRL.NS",
        "ASTRAL.NS", "ATUL.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS",
        "BEL.NS", "BOSCHLTD.NS", "CHOLAFIN.NS", "CUB.NS", "DALBHARAT.NS",
        "DEEPAKNTR.NS", "DHANI.NS", "DLF.NS", "ESCORTS.NS", "EXIDEIND.NS",
        "GAIL.NS", "GODREJIND.NS", "GODREJPROP.NS", "HAL.NS", "HINDPETRO.NS",
        "IDEA.NS", "IGL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDUSTOWER.NS",
        "IRCTC.NS", "JUBLFOOD.NS", "LALPATHLAB.NS", "LAURUSLABS.NS", "MGL.NS",
        "MINDTREE.NS", "MPHASIS.NS", "NAM-INDIA.NS", "NMDC.NS", "OBEROIRLTY.NS",
        "OFSS.NS", "PAGEIND.NS", "PERSISTENT.NS", "PETRONET.NS", "PIIND.NS",
        "POLYCAB.NS", "RADICO.NS", "RAMCOCEM.NS", "RVNL.NS", "SIEMENS.NS",
        "SOLARINDS.NS", "SONATSOFTW.NS", "TATACOMM.NS", "TATAPOWER.NS", "TECHM.NS",
        "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "VEDL.NS", "WHIRLPOOL.NS", "YESBANK.NS",
        "ZOMATO.NS", "PAYTM.NS", "NYKAA.NS", "POLICYBZR.NS", "MAPMYINDIA.NS"
    ]
    
    indian_data = {}
    print(f"Downloading {len(all_indian_stocks)} Indian stocks...")
    
    for ticker in tqdm(all_indian_stocks, desc="Indian Stocks"):
        try:
            data = yf.download(ticker, period=period, progress=False)
            if len(data) > 50:  # Lower threshold from 100 to 50
                data = calculate_technical_indicators(data)
                data = data.dropna()
                if len(data) > 30:  # Lower threshold from 50 to 30
                    indian_data[ticker] = data
                    # Debug: print first successful stock
                    if len(indian_data) == 1:
                        print(f"\n✓ First stock successfully processed: {ticker} ({len(data)} rows)")
        except Exception as e:
            continue
        time.sleep(0.1)  # Rate limiting
    
    print(f"Successfully downloaded {len(indian_data)} Indian stocks")
    return indian_data


def download_all_us_stocks(period="1y"):
    """
    Download comprehensive list of US stocks (300+ stocks)
    
    Args:
        period: Period for historical data (default: 1y)
        
    Returns:
        Dictionary of ticker: DataFrame
    """
    # Extended US stock list (300+ stocks)
    all_us_stocks = [
        # Technology
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "ADBE", "NFLX", "CRM",
        "ORCL", "CSCO", "INTC", "IBM", "QCOM", "TXN", "AVGO", "AMD", "NOW", "SNOW",
        "UBER", "LYFT", "SHOP", "SQ", "PYPL", "ZM", "DOCU", "CRWD", "PANW", "FTNT",
        
        # Financials
        "JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "V", "MA", "PYPL",
        "SCHW", "BLK", "SPGI", "MCO", "ICE", "CME", "NDAQ", "TROW", "AJG", "MMC",
        
        # Healthcare
        "JNJ", "PFE", "MRK", "ABT", "TMO", "DHR", "LLY", "UNH", "CVS", "ANTM",
        "GILD", "AMGN", "BIIB", "REGN", "VRTX", "ILMN", "ISRG", "SYK", "BDX", "BSX",
        
        # Consumer
        "PG", "KO", "PEP", "WMT", "TGT", "COST", "HD", "LOW", "NKE", "MCD",
        "SBUX", "YUM", "CL", "EL", "KMB", "GIS", "K", "HSY", "TAP", "STZ",
        
        # Industrial
        "BA", "CAT", "DE", "GE", "HON", "MMM", "UTX", "LMT", "RTX", "NOC",
        "GD", "EMR", "ITW", "ETN", "ROK", "SWK", "FAST", "SNA", "DOV", "PNR",
        
        # Energy
        "XOM", "CVX", "COP", "SLB", "EOG", "PSX", "MPC", "VLO", "OXY", "DVN",
        "HAL", "BKR", "KMI", "WMB", "OKE", "APA", "MRO", "FANG", "PXD", "HES",
        
        # Materials
        "LIN", "APD", "ECL", "NEM", "FCX", "DD", "PPG", "SHW", "ALB", "CE",
        "NUE", "STLD", "RS", "AVY", "WRK", "IP", "PKG", "SEE", "BALL", "CCK",
        
        # Real Estate
        "AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "DLR", "WELL", "AVB",
        "EQR", "VTR", "ARE", "BXP", "SLG", "KIM", "FRT", "REG", "UDR", "ESS",
        
        # Utilities
        "NEE", "DUK", "D", "SO", "AEP", "EXC", "SRE", "XEL", "WEC", "ED",
        "PEG", "FE", "AES", "EIX", "ETR", "CMS", "LNT", "ATO", "AWK", "CNP",
        
        # Communication
        "T", "VZ", "TMUS", "CMCSA", "DIS", "NFLX", "CHTR", "FOXA", "DISH", "LUMN",
        "VIAC", "DISCA", "DISCK", "TTWO", "EA", "ATVI", "TTD", "ROKU", "SNAP", "PINS",
        
        # Additional growth stocks
        "SE", "MELI", "JD", "BIDU", "BABA", "PDD", "TCEHY", "NTES", "WB", "DOYU",
        "FUTU", "IQ", "NIO", "XPEV", "LI", "BYDDY", "TSM", "ASML", "SONY", "NTDOY"
    ]
    
    us_data = {}
    print(f"Downloading {len(all_us_stocks)} US stocks...")
    
    for ticker in tqdm(all_us_stocks, desc="US Stocks"):
        try:
            data = yf.download(ticker, period=period, progress=False)
            if len(data) > 50:  # Lower threshold from 100 to 50
                data = calculate_technical_indicators(data)
                data = data.dropna()
                if len(data) > 30:  # Lower threshold from 50 to 30
                    us_data[ticker] = data
        except:
            continue
        time.sleep(0.1)  # Rate limiting
    
    print(f"Successfully downloaded {len(us_data)} US stocks")
    return us_data


def download_stock_with_fallback(symbol, period="2y"):
    """
    Download stock data with fallback mechanisms
    For Indian stocks, try nsepy first, then yfinance
    For US stocks, use yfinance
    
    Args:
        symbol: Stock symbol
        period: Period for historical data
        
    Returns:
        DataFrame with stock data
    """
    # Check if it's an Indian stock
    is_indian = symbol.endswith('.NS') or symbol.endswith('.BO')
    
    if is_indian and NSEPY_AVAILABLE:
        # Try nsepy first for Indian stocks
        try:
            end_date = date.today()
            if period == "1y":
                start_date = end_date - timedelta(days=365)
            elif period == "2y":
                start_date = end_date - timedelta(days=730)
            elif period == "5y":
                start_date = end_date - timedelta(days=1825)
            else:
                start_date = end_date - timedelta(days=730)
            
            data = download_nse_data(symbol, start_date, end_date)
            if data is not None and len(data) > 50:
                print(f"✓ Downloaded {symbol} from NSE using nsepy")
                return data
        except Exception as e:
            print(f"nsepy failed for {symbol}, falling back to yfinance: {e}")
    
    # Fallback to yfinance
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        
        if data.empty:
            return None
        
        data = calculate_technical_indicators(data)
        data = data.dropna()
        
        print(f"✓ Downloaded {symbol} using yfinance")
        return data
        
    except Exception as e:
        print(f"Error downloading {symbol}: {e}")
        return None
