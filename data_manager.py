import os
import pandas as pd
import pytz
from datetime import timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from config import DATA_DIR

class DataManager:
    def __init__(self, api_key, secret_key):
        self.client = StockHistoricalDataClient(api_key, secret_key)
        self.ny_tz = pytz.timezone('America/New_York')

    def get_data(self, symbol, start_date, end_date, timeframe=TimeFrame.Minute):
        """
        Primary: Parquet.
        Backup: CSV.
        Logic: Reads Parquet to check dates, but writes to BOTH when updating.
        """
        tf_tag = "1Min" if timeframe == TimeFrame.Minute else "1Day"
        
        # Define BOTH paths
        parquet_path = os.path.join(DATA_DIR, f"{symbol}_{tf_tag}.parquet")
        csv_path = os.path.join(DATA_DIR, f"{symbol}_{tf_tag}.csv")
        
        req_start = self.ny_tz.localize(start_date)
        req_end = self.ny_tz.localize(end_date)
        
        # 1. IF NO PARQUET EXISTS: Download everything & Save Both
        if not os.path.exists(parquet_path):
            print(f"No local data for {symbol}. Downloading full history...")
            df = self._fetch_from_alpaca(symbol, req_start, req_end, timeframe)
            if not df.empty:
                self._save_to_disk(df, parquet_path, csv_path) # <--- Helper function
            return df

        # 2. IF PARQUET EXISTS: Load it and check gaps
        print(f"Found local {tf_tag} data for {symbol}. Checking for gaps...")
        df = pd.read_parquet(parquet_path)
        
        local_start = df.index[0]
        local_end = df.index[-1]
        is_updated = False
        
        # --- CHECK BACKWARD (PREPEND) ---
        if req_start < local_start:
            print(f"   Downloading missing history: {req_start.date()} -> {local_start.date()}")
            prepend_df = self._fetch_from_alpaca(symbol, req_start, local_start, timeframe)
            if not prepend_df.empty:
                df = pd.concat([prepend_df, df])
                is_updated = True
        
        # --- CHECK FORWARD (APPEND) ---
        if req_end > local_end:
            print(f"   Downloading new data: {local_end.date()} -> {req_end.date()}")
            buffer = timedelta(minutes=1) if timeframe == TimeFrame.Minute else timedelta(days=1)
            append_df = self._fetch_from_alpaca(symbol, local_end + buffer, req_end, timeframe)
            if not append_df.empty:
                df = pd.concat([df, append_df])
                is_updated = True
        
        # 3. SAVE BOTH IF CHANGED
        if is_updated:
            print(f"   Saving merged data ({len(df)} rows) to Parquet and CSV...")
            # Sort and Drop Duplicates
            df = df.sort_index()
            df = df[~df.index.duplicated(keep='last')]
            
            # Save to both locations
            self._save_to_disk(df, parquet_path, csv_path)
        else:
            print("   Local data covers the requested range.")
            
            # Edge Case: If Parquet exists but User deleted CSV manually, re-create CSV
            if not os.path.exists(csv_path):
                print("   (Restoring missing CSV backup...)")
                df.to_csv(csv_path)

        return df.loc[req_start:req_end]

    def _save_to_disk(self, df, parquet_path, csv_path):
        """Helper to ensure we always save both at the same time"""
        # 1. Save Primary (Fast)
        df.to_parquet(parquet_path)
        # 2. Save Backup (Readable)
        df.to_csv(csv_path)

    def _fetch_from_alpaca(self, symbol, start, end, timeframe):
        # (This function remains exactly the same as before)
        req = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=timeframe,
            start=start,
            end=end
        )
        try:
            bars = self.client.get_stock_bars(req)
            if bars.data:
                df = bars.df.reset_index()
                df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
                df['timestamp'] = df['timestamp'].dt.tz_convert('America/New_York')
                df = df.set_index('timestamp')
                
                if timeframe == TimeFrame.Minute:
                    df = df.between_time('09:30', '16:00')
                
                return df[['Open', 'High', 'Low', 'Close', 'Volume']]
            return pd.DataFrame()
        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()
