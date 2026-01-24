import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover
from Indicators import rsi, bollinger_bands
from backtesting.test import SMA

# --- STRATEGY CLASSES ---
class SmaCross(Strategy):
    """
    Simple Moving Average (SMA) Crossover Strategy.
    
    LOGIC:
    1. ENTRY (Long):
       - Fast SMA (n1) crosses ABOVE Slow SMA (n2).
       - This signals upward momentum (Golden Cross).

    2. EXIT:
       - Fast SMA (n1) crosses BELOW Slow SMA (n2).
       - This signals downward momentum (Death Cross).
    """
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

class MeanReversion(Strategy):
    """
    Bollinger Band Mean Reversion Strategy.
    
    LOGIC:
    1. ENTRY (Long):
       - Price closes BELOW the Lower Bollinger Band.
       - RSI is BELOW the Oversold threshold (e.g. 30).
       
    2. EXIT:
       - Price reverts back to the Middle Bollinger Band (SMA).
       - OR RSI becomes Overbought (e.g. 70).
    """
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
            rsi, 
            pd.Series(self.data.Close), 
            self.rsi_period, 
            overlay=False,  # <--- THIS IS THE FIX
            name = f"RSI({self.rsi_period})"
        )

        # 2. Compute Bollinger Bands
        # Since our function returns 3 arrays, we unpack them
        # 1. UPPER BAND
        self.upper = self.I(
            lambda: bollinger_bands(pd.Series(self.data.Close), self.bb_period, self.bb_std)[0],
            overlay=True,
            name="UpperBB",
            color="purple"
        )

        # 2. MIDDLE BAND
        self.middle = self.I(
            lambda: bollinger_bands(pd.Series(self.data.Close), self.bb_period, self.bb_std)[1],
            overlay=True,
            name="MidBB",
            color="pink"
        )

        # 3. LOWER BAND
        self.lower = self.I(
            lambda: bollinger_bands(pd.Series(self.data.Close), self.bb_period, self.bb_std)[2],
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
