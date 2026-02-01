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
    MACD Momentum Crossover Strategy
    
    OVERVIEW:
    This strategy captures market momentum by tracking the relationship between 
    short-term (Fast) and long-term (Slow) moving averages. It aims to enter 
    trends as they accelerate and exit when momentum fades.

    LOGIC:
    1. ENTRY (Long): 
       - Triggered when the MACD Line crosses ABOVE the Signal Line (Golden Cross).
       - Indicates bullish momentum is increasing.
       
    2. EXIT:
       - Triggered when the MACD Line crosses BELOW the Signal Line (Death Cross).
       - Indicates bullish momentum is weakening or reversing.

    INDICATORS:
    - MACD Line: Difference between 12-period and 26-period EMAs.
    - Signal Line: 9-period EMA of the MACD Line.
    - Histogram: Visual difference between MACD and Signal (plotted separately).
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
        

        
        

        
