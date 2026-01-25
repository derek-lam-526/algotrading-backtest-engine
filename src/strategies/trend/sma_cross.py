import pandas as pd
import numpy as np
from strategies.base import BaseStrategy
from backtesting.lib import crossover
from backtesting.test import SMA

class SmaCross(BaseStrategy):
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
