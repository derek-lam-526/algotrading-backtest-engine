import os
import pandas as pd
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from backtesting import Backtest

import config
from core.data_manager import DataManager
import strategies
from core.report_manager import ReportGenerator

def check_api_loaded():
    print(f"API Key Loaded: {'Yes' if config.API_KEY else 'No'}")

def run_simple_backtest():
    # Configure backtest
    SYMBOL = "KO"
    START = datetime(2022, 12, 1)
    END = datetime(2026, 1, 1)
    # END = datetime.today() - timedelta(days = 1)
    STRATEGY_CLASS = strategies.LrcReversion
    TF = TimeFrame(1, TimeFrameUnit.Hour) # Minute, Hour, Day, Week, Month
    INITIAL_CASH = 50000
    COMMISSION = (0.35, 0.001) # (minimum charge, percentage)

    # Check if API key loaded
    check_api_loaded()

    # Initialise
    print("--- Starting Backtest Engine ---")
    dm = DataManager(config.API_KEY, config.SECRET_KEY)

    # Get Data
    df = dm.get_data(SYMBOL, START, END, timeframe=TF)
    
    if not os.path.exists(config.OUTPUT_DIR):
        os.makedirs(config.OUTPUT_DIR)
        print(f"Created directory: {config.OUTPUT_DIR}")

    if not df.empty:
        # Remove timezone for backtest
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        print(f"Running backtest on {len(df)} candles...")
        
        # Run Backtest
        bt = Backtest(df, STRATEGY_CLASS, cash=INITIAL_CASH, commission=COMMISSION)
        stats = bt.run()
        
        s_sym = pd.Series([SYMBOL], index=['Symbol'])
        stats = pd.concat([s_sym, stats])
        
        # Save
        ReportGenerator.save_report(backtest_instance=bt, 
                                    stats=stats, 
                                    symbol=SYMBOL, 
                                    timeframe=TF, 
                                    strategy_class=STRATEGY_CLASS, 
                                    output_dir=config.OUTPUT_DIR)
        
    else:
        print("No data available.")

if __name__ == "__main__":
    run_simple_backtest()
