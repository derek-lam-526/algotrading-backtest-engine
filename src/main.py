import os
import pandas as pd
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from backtesting import Backtest

import config
import backtest_settings as settings

from core.data_manager import DataManager
from core.report_manager import ReportGenerator

class BacktestEngine:
    def __init__(self, strategy_class):
        self.strategy_class = strategy_class
        self.output_dir = config.OUTPUT_DIR

        # Check for API key 
        if config.API_KEY:
            self.dm = DataManager(config.API_KEY, config.SECRET_KEY)
        else:
            raise ValueError("API_KEY missing in config.py")
        
        # Prepare output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def run(self):
        mode = settings.RUN_MODE.upper()
        print(f"Engine Started | Mode: {mode} | Strategy: {self.strategy_class.__name__}")

        match mode:
            case "SINGLE":
                self._run_single()
            case _:
                print(f"Unknown Mode: '{mode}'. Check backtest_settings.py")

    def _run_single(self):
        symbol = settings.SINGLE_SYMBOL
        self._process_symbol(symbol)

    def _run_batch(self):
        pass

    def _process_symbol(self, symbol):
        """
            The Core Worker: 
            1. Fetches Data 
            2. Runs Backtest 
            3. Saves Report
        """
        try:
            print(f"   Processing {symbol}...", end=" ")
            
            # Get Data
            df = self.dm.get_data(symbol, 
                                  settings.START_DATE, 
                                  settings.END_DATE, 
                                  timeframe=settings.TIMEFRAME)
            
            if df.empty:
                print(f"No data found for {symbol}. Skipping.")
                return False
            
            # Remove timezone for backtest
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            # Run Backtest
            bt = Backtest(df, 
                          self.strategy_class, 
                          cash=settings.INITIAL_CASH, 
                          commission=settings.COMMISSION)
            
            # Run with parameter overrides from settings
            stats = bt.run(**settings.STRATEGY_PARAMS)
            
            s_sym = pd.Series([symbol], index=['Symbol'])
            stats = pd.concat([s_sym, stats])
            
            # Save
            ReportGenerator.save_report(backtest_instance=bt, 
                                        stats=stats, 
                                        symbol=settings.SINGLE_SYMBOL, 
                                        timeframe=settings.TIMEFRAME, 
                                        strategy_class=stats._strategy, 
                                        output_dir=self.output_dir)
            print("Done.")
            return True
        
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            # Uncomment the next line to see full error tracebacks during debugging
            import traceback; traceback.print_exc()
            return False
    
def main():
    bt_engine = BacktestEngine(strategy_class = settings.ACTIVE_STRATEGY)
    bt_engine.run()

if __name__ == "__main__":
    main()
