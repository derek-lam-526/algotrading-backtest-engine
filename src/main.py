import os
import pandas as pd
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from backtesting import Backtest

import config
from core.data_manager import DataManager
from strategies import BollingerReversion, SmaCross, MonthlyDCA
from core.report_manager import ReportGenerator

def check_api_loaded():
    print(f"API Key Loaded: {'Yes' if config.API_KEY else 'No'}")

def run_simple_backtest():
    # Configure backtest
    SYMBOL = "VOO"
    START = datetime(2023, 1, 1)
    END = datetime(2026, 1, 15)
    # END = datetime.today() - timedelta(days = 1)
    STRATEGY_CLASS = MonthlyDCA
    TF = TimeFrame(1, TimeFrameUnit.Day) # Minute, Hour, Day, Week, Month
    INITIAL_CASH = 50000
    COMMISSION = (0.35, 0.001) # (minimum charge, percentage)

    # Check if API key loaded
    check_api_loaded()

    # Initialise
    print("--- Starting Backtest Engine ---")
    dm = DataManager(config.API_KEY, config.SECRET_KEY)

    # Get Data
    df = dm.get_data(SYMBOL, START, END, timeframe=TF)
    print(df.tail().index.dtype)
    
    if not os.path.exists(config.OUTPUT_DIR):
        os.makedirs(config.OUTPUT_DIR)
        print(f"Created directory: {config.OUTPUT_DIR}")

    if not df.empty:
        print(f"Running backtest on {len(df)} candles...")
        
        # Run Backtest
        bt = Backtest(df, STRATEGY_CLASS, cash=INITIAL_CASH, commission=COMMISSION)
        stats = bt.run()
        
        s_sym = pd.Series([SYMBOL], index=['Symbol'])
        stats = pd.concat([s_sym, stats])
        
        print(stats)

        strat_name = STRATEGY_CLASS.__name__
        date_str = f"{START.strftime('%Y%m%d')}-{END.strftime('%Y%m%d')}"
        return_pct = round(stats['Return [%]'], 2)
        
        # Construct Final Name
        filename = f"{SYMBOL}_{strat_name}_{date_str}_{TF.value}_Ret{return_pct}.html"
        
        full_path = os.path.join(config.OUTPUT_DIR, filename)
        
        # Save
        ReportGenerator.save_report(bt, stats, full_path, strategy_class=STRATEGY_CLASS)
        print(f"\nPlot saved to: {full_path}")
        # print(stats._trades)
        # print(stats._equity_curve)
        
    else:
        print("No data available.")

if __name__ == "__main__":
    run_simple_backtest()
