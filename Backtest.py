import os
import pandas as pd
from datetime import datetime, timedelta
import pytz
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
from report_manager import ReportGenerator

# ==========================================
# 1. CONFIGURATION
# ==========================================
API_KEY = "PKQHQDBXXJS7OCYX5PWSAXV3TX"
SECRET_KEY = "7mAQkxwsCfbKcS7SxZ1RYxAhczJrUjvqMFQsYECxDd1t"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")


# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ==========================================
# 2. DATA MANAGER (The "Engine")
# ==========================================
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
# ==========================================
# 3. STRATEGY (The Logic)
# ==========================================
def indicator_rsi(series, period=14):
    """Calculate RSI using Pandas (Wilder's Smoothing)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    # First simple average
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    
    # Wilder's Smoothing (Standard for RSI)
    # This creates a dependency on previous values, so we use pandas iteration or ewm
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def indicator_bollinger(series, period=20, std_dev=2):
    """Returns Upper, Middle, and Lower Bands"""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower

class MeanReversion(Strategy):
    # Parameters we can optimize later
    rsi_period = 14
    bb_period = 20
    bb_std = 2.0
    oversold = 35
    overbought = 65
    
    def init(self):
        # 1. Compute RSI
        # self.I wraps the function so it appears on the chart
        self.rsi = self.I(
            indicator_rsi, 
            pd.Series(self.data.Close), 
            self.rsi_period, 
            overlay=False,  # <--- THIS IS THE FIX
            name = f"RSI({self.rsi_period})"
        )

        # 2. Compute Bollinger Bands
        # Since our function returns 3 arrays, we unpack them
        # 1. UPPER BAND
        self.upper = self.I(
            lambda: indicator_bollinger(pd.Series(self.data.Close), self.bb_period, self.bb_std)[0],
            overlay=True,
            name="UpperBB",
            color="purple"
        )

        # 2. MIDDLE BAND
        self.middle = self.I(
            lambda: indicator_bollinger(pd.Series(self.data.Close), self.bb_period, self.bb_std)[1],
            overlay=True,
            name="MidBB",
            color="pink"
        )

        # 3. LOWER BAND
        self.lower = self.I(
            lambda: indicator_bollinger(pd.Series(self.data.Close), self.bb_period, self.bb_std)[2],
            overlay=True,
            name="LowerBB",
            color="yellow"
        )

    def next(self):
        price = self.data.Close[-1]
        
        # ENTRY LOGIC:
        # If we are NOT in a position...
        if not self.position:
            # AND Price is below Lower Band (Cheap)
            if price < self.lower[-1]:
                # AND RSI is Oversold (Exhausted)
                if self.rsi[-1] < self.oversold:
                    self.buy()
        
        # EXIT LOGIC:
        # If we ARE in a position...
        else:
            # If RSI gets too hot (Overbought)
            if self.rsi[-1] > self.overbought:
                self.position.close()
            # OR price reverts back to the mean (Middle Band)
            elif price > self.middle[-1]:
                self.position.close()

class SmaCross(Strategy):
    n1 = 10
    n2 = 20

    def init(self):
        # Calculate moving averages
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)

    def next(self):
        # Buy if SMA1 crosses above SMA2
        if crossover(self.sma1, self.sma2):
            self.buy()
        
        # Sell if SMA1 crosses below SMA2
        elif crossover(self.sma2, self.sma1):
            self.position.close()

# ==========================================
# 4. EXECUTION (The Main Loop)
# ==========================================
# ... (Previous imports and class definitions)

if __name__ == "__main__":
    # A. Setup Manager
    dm = DataManager(API_KEY, SECRET_KEY)
    
    # B. Define parameters
    SYMBOL = "MU"
    START = datetime(2022, 1, 1)
    END = datetime(2025, 1, 23)
 
    STRATEGY_CLASS = MeanReversion  

    # TF = TimeFrame.Minute
    TF = TimeFrame.Day 
    
    # The system automatically handles the rest
    df = dm.get_data(SYMBOL, START, END, timeframe=TF)
    
    # SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
    # RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
    
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        print(f"Created directory: {RESULTS_DIR}")

    if not df.empty:
        print(f"Running backtest on {len(df)} candles...")
        
        # Run Backtest
        bt = Backtest(df, STRATEGY_CLASS, cash=10000, commission=.002)
        stats = bt.run()
        print(stats)

        strat_name = STRATEGY_CLASS.__name__
        date_str = f"{START.strftime('%Y%m%d')}-{END.strftime('%Y%m%d')}"
        return_pct = round(stats['Return [%]'], 2)
        
        # Construct Final Name
        filename = f"{SYMBOL}_{strat_name}_{date_str}_Ret{return_pct}.html"
        
        full_path = os.path.join(RESULTS_DIR, filename)
        
        # Save
        # bt.plot(filename=plot_file, open_browser=False)
        ReportGenerator.save_report(bt, stats, full_path)
        print(f"\nPlot saved to: {full_path}")
        
    else:
        print("No data available.")
