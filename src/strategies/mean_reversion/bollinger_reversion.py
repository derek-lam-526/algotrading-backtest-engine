import pandas as pd
from strategies.base import BaseStrategy
from indicators.technical import rsi, bollinger_bands # Assuming you moved your math here

class BollingerReversion(BaseStrategy):
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
    rsi_period = 14
    bb_period = 20
    bb_std = 2.0
    oversold = 35
    overbought = 65
    
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
        # Note: We use lambdas to unpack the tuple (Upper, Mid, Lower)
        # Ideally, move this unpacking logic to indicators/technical.py for cleaner code
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
