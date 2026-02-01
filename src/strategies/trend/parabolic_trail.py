import numpy as np
import pandas as pd
import pandas_ta as ta
from strategies.base import BaseStrategy 
from backtesting.lib import crossover

def get_psar_ta(high, low, close, af0, af, max_af):
    h = pd.Series(high)
    l = pd.Series(low)
    c = pd.Series(close)
    
    df = ta.psar(high=h, low=l, close=c, af0=af0, af=af, max_af=max_af)

    combined = df.iloc[:, 0].combine_first(df.iloc[:, 1])

    return combined.values

def get_sma_ta(close, window):
    c = pd.Series(close)
    df = ta.sma(close=c, length=window)

    return df.values

def get_bbands_lower_ta(close, length, lower_std=2, upper_std=2):
    c = pd.Series(close)
    df = ta.bbands(close=c, length=length, lower_std=lower_std, upper_std=upper_std)

    return df.iloc[:,0].values

class ParabolicTrail(BaseStrategy):
    
    af0 = 0.02
    af = 0.02
    max_af = 0.2
    sl_sma_window = 20
    sl_std_lower = 1

    def init(self):
        super().init()

        # --- Indicators --- 

        # Parabolic SAR
        self.psar = self.I(get_psar_ta,
                           self.data.High,
                           self.data.Low,
                           self.data.Close,
                           self.af0,
                           self.af,
                           self.max_af,
                           overlay=True,
                           scatter=True,
                           color="grey",
                           name="SAR",
                           )
        
        # SMA
        self.sma = self.I(get_sma_ta, 
                          self.data.Close,
                          self.sl_sma_window,
                          overlay=True,
                          name="SMA"
                          )
        
        self.bb_lower = self.I(get_bbands_lower_ta,
                                 self.data.Close,
                                 self.sl_sma_window,
                                 self.sl_std_lower,
                                 overlay=True,
                                 name="BB_Lower"
                                 )
    
    def next(self):
        current_price = self.data.Close[-1]
        current_low = self.data.Low[-1]
        current_psar = self.psar[-1]
        current_sma = self.sma[-1]
        current_bb_lower = self.bb_lower[-1]

        if not self.position:
            if current_price > current_psar:
                entry_sl = (current_low + 2 * current_psar) / 3 
                self.buy(sl = entry_sl)
        
        # Adjust stop loss dyamically
        for trade in self.trades:
            if trade.is_long:
                new_sl = (current_low + 2 * current_psar) / 3 
                if trade.sl:
                    trade.sl = max(trade.sl, new_sl) 
                else:
                    trade.sl = new_sl

        # Exit if SMR go from below to above
        if self.position and crossover(current_psar,current_price):
            self.position.close()
        
        # # Exit if crosses MA -> lost upward momentum
        # if self.position and crossover(current_bb_lower, current_price):
        #     self.position.close()
                
                


        


        
