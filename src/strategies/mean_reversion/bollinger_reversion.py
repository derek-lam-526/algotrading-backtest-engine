import pandas as pd
from strategies.base import BaseStrategy
from indicators.technical import rsi, bollinger_bands # Assuming you moved your math here

class BollingerReversion(BaseStrategy):
    """
    Bollinger Band & RSI Mean Reversion Strategy.

    This strategy identifies oversold conditions by combining statistical extremes
    (Bollinger Bands) with momentum confirmation (RSI). It aims to buy when price
    deviates significantly from its moving average while momentum is weak, and exits
    on mean reversion or momentum recovery.

    PARAMETERS
    ----------
    rsi_period : int (Default: 14)
        The lookback period for the Relative Strength Index (RSI).

    bb_period : int (Default: 50)
        The lookback period for the Bollinger Band Moving Average (Basis).
        
    bb_std : float (Default: 2.0)
        The width of the bands in Standard Deviations.
        
    oversold : int (Default: 30)
        Threshold: RSI must be BELOW this value to confirm a Long Entry.
        
    overbought : int (Default: 80)
        Threshold: If RSI goes ABOVE this value, the position is closed (Panic Exit).

    LOGIC
    -----
    1. ENTRY (Long): 
       - Price crosses below the Lower Bollinger Band (Statistical extreme).
       - AND RSI is below the 'oversold' threshold (Momentum confirmation).
       
    2. EXIT: 
       - Mean Reversion: Price crosses above the midpoint of the Upper and Middle Band.
       - Momentum Exhaustion: RSI exceeds the 'overbought' threshold.
    """

    rsi_period = 14
    bb_period = 50
    bb_std = 2.0
    oversold = 30
    overbought = 80
    
    def init(self):
        super().init()

        # RSI
        self.rsi = self.I(
            rsi, 
            pd.Series(self.data.Close), 
            self.rsi_period, 
            overlay=False,
            name=f"RSI({self.rsi_period})"
        )

        # Bollinger Bands
        self.upper = self.I(lambda: bollinger_bands(pd.Series(self.data.Close), self.bb_period, self.bb_std)[0], 
                            name="UpperBB", overlay=True, color="purple")
        
        self.middle = self.I(lambda: bollinger_bands(pd.Series(self.data.Close), self.bb_period, self.bb_std)[1], 
                             name="MidBB", overlay=True, color="pink")
        
        self.lower = self.I(lambda: bollinger_bands(pd.Series(self.data.Close), self.bb_period, self.bb_std)[2], 
                            name="LowerBB", overlay=True, color="yellow")

    def next(self):
        price = self.data.Close[-1]
        
        if not self.position:
            # Long Entry
            if price < self.lower[-1] and self.rsi[-1] < self.oversold:
                self.buy()
        
        else:
            # Exit Conditions
            if self.rsi[-1] > self.overbought:
                self.position.close()
            # Dynamic Exit: Cross above midpoint of Upper and Middle band
            elif price > (self.middle[-1] + self.upper[-1]) / 2:
                self.position.close()
