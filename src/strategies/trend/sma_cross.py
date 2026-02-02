import pandas as pd
import numpy as np
from strategies.base import BaseStrategy
from backtesting.lib import crossover
from backtesting.test import SMA

class SmaCross(BaseStrategy):
    """
    Simple Moving Average (SMA) Crossover Strategy.

    This is a classic trend-following system that uses two moving averages with 
    different lookback periods to identify shifts in market momentum. It assumes 
    that when the faster average crosses above the slower average, a new uptrend 
    is beginning.

    PARAMETERS
    ----------
    n1 : int (Default: 10)
        The lookback period for the Fast SMA (Signal Line).
        
    n2 : int (Default: 20)
        The lookback period for the Slow SMA (Baseline Trend).

    LOGIC
    -----
    1. ENTRY (Long): 
       - Bullish Crossover (Golden Cross): The Fast SMA (n1) crosses ABOVE the Slow SMA (n2).
       
    2. EXIT: 
       - Bearish Crossover (Death Cross): The Fast SMA (n1) crosses BELOW the Slow SMA (n2).
       - The position is closed immediately upon this reversal signal.
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
