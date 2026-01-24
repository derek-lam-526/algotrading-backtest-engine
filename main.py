import os
from datetime import datetime
from alpaca.data.timeframe import TimeFrame
from backtesting import Backtest

import config
from data_manager import DataManager
from Strategies import MeanReversion, SmaCross
from report_manager import ReportGenerator

if __name__ == "__main__":
    # Initialise
    print("--- Starting Backtest Engine ---")
    dm = DataManager(config.API_KEY, config.SECRET_KEY)
    
    # Configure backtest
    SYMBOL = "MU"
    START = datetime(2023, 1, 1)
    END = datetime(2025, 1, 23)
    STRATEGY_CLASS = SmaCross  
    TF = TimeFrame.Day #TimeFrame.Minute
    
    df = dm.get_data(SYMBOL, START, END, timeframe=TF)
    
    if not os.path.exists(config.RESULTS_DIR):
        os.makedirs(config.RESULTS_DIR)
        print(f"Created directory: {config.RESULTS_DIR}")

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
        
        full_path = os.path.join(config.RESULTS_DIR, filename)
        
        # Save
        ReportGenerator.save_report(bt, stats, full_path, strategy_class=STRATEGY_CLASS)
        print(f"\nPlot saved to: {full_path}")
        
    else:
        print("No data available.")
