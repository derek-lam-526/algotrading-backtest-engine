import os
from datetime import datetime
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from backtesting import Backtest

import config
from core.data_manager import DataManager
from strategies.mean_reversion.bollinger_reversion import BollingerReversion
from strategies.trend.sma_cross import SmaCross
from core.report_manager import ReportGenerator

if __name__ == "__main__":
    # Check if API key loaded
    print(f"API Key Loaded: {'Yes' if config.API_KEY else 'No'}")
    
    # Initialise
    print("--- Starting Backtest Engine ---")
    dm = DataManager(config.API_KEY, config.SECRET_KEY)
    
    # Configure backtest
    SYMBOL = "URG"
    START = datetime(2024, 1, 1)
    END = datetime(2026, 1, 23)
    STRATEGY_CLASS = SmaCross
    TF = TimeFrame(1, TimeFrameUnit.Hour) # Minute, Hour, Day, Week, Month

    # Get Data
    df = dm.get_data(SYMBOL, START, END, timeframe=TF)
    
    if not os.path.exists(config.OUTPUT_DIR):
        os.makedirs(config.OUTPUT_DIR)
        print(f"Created directory: {config.OUTPUT_DIR}")

    if not df.empty:
        print(f"Running backtest on {len(df)} candles...")
        
        # Run Backtest
        bt = Backtest(df, STRATEGY_CLASS, cash=10000, commission=(0.35,0.001))
        stats = bt.run()
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
        
    else:
        print("No data available.")
