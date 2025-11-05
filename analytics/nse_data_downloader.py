"""
NSE Data Downloader - Windows Compatible
Downloads historical NSE bhavcopy data and prepares it for model training
"""

import pandas as pd
import requests
import os
from datetime import datetime, timedelta
import time
import logging
from typing import List, Optional
import numpy as np

class NSEDataDownloader:
    """
    Download and process NSE bhavcopy data for Indian stocks
    Compatible with Windows filesystem and encoding
    """
    
    def __init__(self, base_url: str = "https://archives.nseindia.com/products/content/", 
                 output_dir: str = "nse_data"):
        self.base_url = base_url
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Setup session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # Setup logging
        self.setup_logging()
        
        self.processed_dates = []
        self.failed_dates = []
    
    def setup_logging(self):
        """Setup logging system"""
        log_file = os.path.join(self.output_dir, "nse_downloader.log")
        
        # Clear existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logging.info("🚀 NSE Data Downloader started")
        logging.info(f"📁 Output directory: {os.path.abspath(self.output_dir)}")
    
    def get_trading_days(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Generate list of potential trading days (excluding weekends)"""
        dates = []
        current_date = start_date
        
        while current_date <= end_date:
            # NSE trades Monday to Friday
            if current_date.weekday() < 5:
                dates.append(current_date)
            current_date += timedelta(days=1)
        
        logging.info(f"📅 Generated {len(dates)} potential trading days")
        return dates
    
    def download_bhavcopy(self, date: datetime) -> Optional[pd.DataFrame]:
        """Download and process bhavcopy for a specific date"""
        date_str = date.strftime('%d%m%Y')
        url = f"{self.base_url}sec_bhavdata_full_{date_str}.csv"
        
        try:
            # Retry mechanism for network issues
            for attempt in range(3):
                try:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    if len(response.content) < 1000:
                        logging.debug(f"📭 Empty response for {date_str}")
                        return None
                    
                    break
                    
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < 2:
                        logging.warning(f"⏰ Retry {attempt + 1} for {date_str}")
                        time.sleep(3)
                    else:
                        raise
            
            # Read CSV with proper encoding
            try:
                df = pd.read_csv(
                    pd.io.common.BytesIO(response.content),
                    encoding='utf-8',
                    engine='python'
                )
            except UnicodeDecodeError:
                df = pd.read_csv(
                    pd.io.common.BytesIO(response.content),
                    encoding='latin-1',
                    engine='python'
                )
            
            if df.empty or len(df.columns) < 5:
                return None
            
            # Clean and process data
            df = self.clean_data(df, date)
            
            self.processed_dates.append(date)
            logging.info(f"✅ {date.strftime('%Y-%m-%d')} - {len(df)} records")
            
            return df
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.debug(f"📅 No data for {date_str} (holiday)")
            else:
                logging.warning(f"❌ HTTP error for {date_str}: {e}")
            self.failed_dates.append(date)
            return None
            
        except Exception as e:
            logging.error(f"💥 Error processing {date_str}: {str(e)[:100]}")
            self.failed_dates.append(date)
            return None
    
    def clean_data(self, df: pd.DataFrame, date: datetime) -> pd.DataFrame:
        """Clean and standardize data"""
        # Add date column
        df['DATE'] = date.strftime('%Y-%m-%d')
        
        # Standardize column names
        df.columns = (df.columns
                     .str.strip()
                     .str.upper()
                     .str.replace(' ', '_')
                     .str.replace(r'[^\w_]', '', regex=True))
        
        # Column mapping
        column_mapping = {
            'TOTTRDQTY': 'VOLUME',
            'TOTTRDVAL': 'TURNOVER',
            'TOTALTRADES': 'TOTAL_TRADES',
            'PREVCLOSE': 'PREV_CLOSE',
        }
        df = df.rename(columns=column_mapping)
        
        # Convert numeric columns
        numeric_columns = ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'LAST', 'PREV_CLOSE', 'VOLUME']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = (df[col].astype(str)
                           .str.replace(',', '')
                           .str.replace(r'[^\d.-]', '', regex=True))
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Filter for equity series only
        if 'SERIES' in df.columns:
            df = df[df['SERIES'].isin(['EQ', 'BE'])]
        
        # Clean symbol names
        if 'SYMBOL' in df.columns:
            df['SYMBOL'] = (df['SYMBOL'].astype(str)
                           .str.strip()
                           .str.upper())
        
        return df
    
    def save_batch(self, dataframes: List[pd.DataFrame], batch_num: int):
        """Save batch of dataframes"""
        if not dataframes:
            return
        
        try:
            batch_df = pd.concat(dataframes, ignore_index=True)
            filename = f"batch_{batch_num:03d}.parquet"
            filepath = os.path.join(self.output_dir, filename)
            
            batch_df.to_parquet(filepath, index=False, compression='snappy')
            
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            logging.info(f"💾 Saved {filename} ({file_size_mb:.2f} MB, {len(batch_df)} records)")
            
        except Exception as e:
            logging.error(f"❌ Error saving batch {batch_num}: {e}")
    
    def combine_batches(self, output_file: str):
        """Combine all batch files into final dataset"""
        batch_files = sorted([f for f in os.listdir(self.output_dir) 
                             if f.startswith('batch_') and f.endswith('.parquet')])
        
        if not batch_files:
            logging.error("❌ No batch files found")
            return None
        
        logging.info(f"🔗 Combining {len(batch_files)} batch files...")
        
        try:
            # Read and combine batches
            dataframes = []
            for batch_file in batch_files:
                batch_path = os.path.join(self.output_dir, batch_file)
                df = pd.read_parquet(batch_path)
                dataframes.append(df)
            
            final_df = pd.concat(dataframes, ignore_index=True)
            
            # Check if we have any data
            if len(final_df) == 0:
                logging.error("❌ Combined dataset is empty (0 records)")
                logging.error("   This means no data was downloaded successfully")
                logging.error("   Possible reasons:")
                logging.error("   - All dates were holidays/weekends")
                logging.error("   - Network connection issues")
                logging.error("   - NSE website not accessible")
                return None
            
            # Remove duplicates
            initial_count = len(final_df)
            final_df = final_df.drop_duplicates(subset=['SYMBOL', 'DATE'], keep='first')
            removed = initial_count - len(final_df)
            if removed > 0:
                logging.info(f"🧹 Removed {removed} duplicates")
            
            # Sort data
            final_df = final_df.sort_values(['SYMBOL', 'DATE'])
            
            # Save final dataset
            base_name = output_file.replace('.csv', '')
            
            # Save as Parquet (efficient for large data)
            parquet_path = os.path.join(self.output_dir, f"{base_name}.parquet")
            final_df.to_parquet(parquet_path, index=False, compression='snappy')
            
            # Also save as CSV for compatibility
            csv_path = os.path.join(self.output_dir, f"{base_name}.csv")
            final_df.to_csv(csv_path, index=False)
            
            # Generate summary
            self.generate_summary(final_df, base_name)
            
            logging.info(f"🎉 Final dataset saved:")
            logging.info(f"   📊 Parquet: {parquet_path}")
            logging.info(f"   📄 CSV: {csv_path}")
            logging.info(f"   📈 Total records: {len(final_df):,}")
            logging.info(f"   📅 Date range: {final_df['DATE'].min()} to {final_df['DATE'].max()}")
            logging.info(f"   🔤 Unique symbols: {final_df['SYMBOL'].nunique()}")
            
            # Clean up batch files
            for batch_file in batch_files:
                os.remove(os.path.join(self.output_dir, batch_file))
            
            logging.info("🧹 Batch files cleaned up")
            
            return final_df
            
        except Exception as e:
            logging.error(f"❌ Error combining batches: {e}")
            return None
    
    def generate_summary(self, df: pd.DataFrame, base_name: str):
        """Generate summary statistics"""
        summary = []
        summary.append("=" * 60)
        summary.append("NSE STOCK DATA SUMMARY")
        summary.append("=" * 60)
        summary.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"Total records: {len(df):,}")
        summary.append(f"Date range: {df['DATE'].min()} to {df['DATE'].max()}")
        summary.append(f"Unique symbols: {df['SYMBOL'].nunique()}")
        summary.append(f"Processed dates: {len(self.processed_dates)}")
        summary.append(f"Failed dates: {len(self.failed_dates)}")
        summary.append("")
        summary.append("Top 20 stocks by trading volume:")
        
        # Get top stocks
        top_stocks = (df.groupby('SYMBOL')['VOLUME']
                     .sum()
                     .sort_values(ascending=False)
                     .head(20))
        
        for symbol, volume in top_stocks.items():
            summary.append(f"  {symbol}: {volume:,.0f}")
        
        # Save summary
        summary_path = os.path.join(self.output_dir, f"{base_name}_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary))
        
        logging.info(f"📊 Summary saved: {summary_path}")
    
    def download_data(self, start_date: datetime, end_date: datetime, 
                     output_file: str = 'nse_stock_data.csv',
                     batch_size: int = 30,
                     delay_between_requests: float = 2.0):
        """Main method to download NSE data"""
        logging.info("🚀 Starting NSE Data Download")
        logging.info(f"📅 Date Range: {start_date.date()} to {end_date.date()}")
        logging.info(f"💾 Output: {output_file}")
        logging.info(f"📦 Batch Size: {batch_size} days")
        
        trading_days = self.get_trading_days(start_date, end_date)
        all_data = []
        batch_count = 0
        
        logging.info(f"📥 Downloading data for {len(trading_days)} trading days...")
        
        for i, date in enumerate(trading_days, 1):
            progress = (i / len(trading_days)) * 100
            
            if i % 10 == 0 or i == 1:  # Log every 10 dates
                logging.info(f"📊 Progress: {i}/{len(trading_days)} ({progress:.1f}%)")
            
            df = self.download_bhavcopy(date)
            if df is not None:
                all_data.append(df)
            
            # Save batch
            if len(all_data) >= batch_size:
                batch_count += 1
                self.save_batch(all_data, batch_count)
                all_data = []
            
            # Respectful delay
            time.sleep(delay_between_requests)
        
        # Save remaining data
        if all_data:
            batch_count += 1
            self.save_batch(all_data, batch_count)
        
        # Check if any data was collected
        if batch_count == 0:
            logging.error("❌ No data was downloaded!")
            logging.error(f"   Attempted {len(trading_days)} dates")
            logging.error(f"   All {len(self.failed_dates)} attempts failed")
            logging.error("   Please check:")
            logging.error("   1. Internet connection")
            logging.error("   2. NSE website accessibility")
            logging.error("   3. Date range (may all be holidays)")
            return None
        
        # Combine all batches
        final_df = self.combine_batches(output_file)
        
        # Final report
        if final_df is not None and len(final_df) > 0:
            success_rate = (len(self.processed_dates) / len(trading_days)) * 100
            logging.info(f"✅ Download completed!")
            logging.info(f"   Success rate: {success_rate:.1f}%")
            logging.info(f"   Processed: {len(self.processed_dates)} days")
            logging.info(f"   Failed: {len(self.failed_dates)} days")
            
            return final_df
        else:
            logging.error("❌ Failed to create final dataset")
            return None


if __name__ == "__main__":
    print("=" * 70)
    print("NSE DATA DOWNLOADER - Historical Bhavcopy Data")
    print("=" * 70)
    print()
    
    # Initialize downloader
    downloader = NSEDataDownloader(output_dir="nse_data")
    
    # Define date range - 5 YEARS OF DATA (2020-2024)
    start_date = datetime(2020, 1, 1)  # Start from 2020
    end_date = datetime(2024, 12, 31)  # Until end of 2024
    
    total_days = (end_date - start_date).days
    print(f"📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"📆 Total Days: {total_days} days (~{total_days/365:.1f} years)")
    print(f"💾 Output Directory: nse_data/")
    print()
    print("⚠️  This will download ~5 years of NSE bhavcopy data")
    print("⏱️  Estimated time: 2-4 hours")
    print("💽 Storage required: ~500 MB - 1 GB")
    print()
    
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print()
        print("🚀 Starting download...")
        print("💡 Tip: You can press Ctrl+C to stop at any time")
        print()
        
        try:
            final_df = downloader.download_data(
                start_date=start_date,
                end_date=end_date,
                output_file='nse_stock_data_2020_2024.csv',
                batch_size=20,  # Save every 20 days
                delay_between_requests=2.0  # 2 seconds between requests
            )
            
            if final_df is not None:
                print()
                print("=" * 70)
                print("🎉 DOWNLOAD COMPLETED SUCCESSFULLY!")
                print("=" * 70)
                print()
                print(f"📊 Total Records: {len(final_df):,}")
                print(f"🔤 Unique Stocks: {final_df['SYMBOL'].nunique()}")
                print(f"📅 Date Range: {final_df['DATE'].min()} to {final_df['DATE'].max()}")
                print()
                print("📁 Files created:")
                print("   • nse_data/nse_stock_data_2020_2024.parquet")
                print("   • nse_data/nse_stock_data_2020_2024.csv")
                print("   • nse_data/nse_stock_data_2020_2024_summary.txt")
                print()
                print("🚀 Next step: Run train_indian_models.py to train LSTM models")
            else:
                print("❌ Download failed. Check nse_data/nse_downloader.log for details")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Download interrupted by user")
            print("💡 Partial data may be saved in batch files")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Download cancelled")
