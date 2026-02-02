import pandas as pd 
import pandas_ta as ta 
import numpy as np
from strategies.base import BaseStrategy
from backtesting.lib import crossover

def get_macd(close, fast, slow, signal, hist=False):
    macd_df = ta.macd(close=close,
                    fast=fast,
                    slow=slow,
                    signal=signal,
                    )
    if not hist:
        return macd_df.iloc[:,0].values, macd_df.iloc[:,2].values # MACD, MACD_signal
    return macd_df.iloc[:,1].values # MACD_hist

class MacdCross(BaseStrategy):
    """
    Moving Average Convergence Divergence (MACD) Trend Strategy.

    This is a classic momentum strategy based on the convergence and divergence 
    of two exponential moving averages. It assumes that when the MACD line crosses 
    above its signal line, momentum is shifting bullish, and vice versa. It is an 
    always-in (or stop-and-reverse) system in its current configuration.

    PARAMETERS
    ----------
    macd_fast : int (Default: 12)
        The lookback period for the Fast EMA (Short-term trend).
        
    macd_slow : int (Default: 26)
        The lookback period for the Slow EMA (Long-term trend).
        
    macd_signal : int (Default: 9)
        The smoothing period applied to the MACD line to generate the Signal Line.

    LOGIC
    -----
    1. ENTRY (Long): 
       - Bullish Crossover: The MACD line crosses ABOVE the Signal line.
       - This indicates short-term momentum is rising faster than the long-term average.
       
    2. EXIT: 
       - Bearish Crossover: The MACD line crosses BELOW the Signal line.
       - The position is closed immediately when momentum flips bearish.
    """
    
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9

    def init(self):
        super().init()

        # Define Indicators
        
        self.macd_bundle = self.I(get_macd,
                                  pd.Series(self.data.Close),
                                  self.macd_fast,
                                  self.macd_slow,
                                  self.macd_signal,
                                  False,
                                  name=["MACD","MACD_signal"],
                                  overlay=False)
        
        self.macd_hist = self.I(get_macd,
                                pd.Series(self.data.Close),
                                self.macd_fast,
                                self.macd_slow,
                                self.macd_signal,
                                True,
                                name="MACD_hist",
                                overlay=False)
    
    def next(self):
        current_macd = self.macd_bundle[0]
        current_signal = self.macd_bundle[1]

        # --- Simple Version ---

        # Long entry: MACD > Signal
        if crossover(current_macd, current_signal):
            self.buy()
        
        # Close: Signal < MACD
        if crossover(current_signal, current_macd):
            self.position.close()

        # --- Complex Version ---
        # buy_regime = False

        # if crossover(current_macd, current_signal):
        #     buy_regime = True 

        # if crossover(current_signal, current_macd):
        #     buy_regime = False 
        
        # # Entry: MACD > Signal; and MACD > 0
        # if buy_regime and current_macd > 0:
        #     self.buy()
        
        # # Exit: MACD < Signal; or MACD < 0
        # if not buy_regime and (self.position.is_long or current_macd < 0):
        #     self.position.close()
        

        
        

        
