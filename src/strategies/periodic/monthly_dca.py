import math
import pandas as pd
from strategies.base import BaseStrategy

class MonthlyDCA(BaseStrategy):
    
    monthly_contribution = 2000

    def init(self):
        super().init()

        all_dates = self.data.index
        # Pick the second to last date
        if len(all_dates) > 2:
            self.force_close_date = all_dates[-2]
        else:
            self.force_close_date = None # Data too short to backtest
    
    def next(self):
        if len(self.data) < 2:
            return 
        
        current_date = pd.to_datetime(self.data.index[-1])
        previous_date = pd.to_datetime(self.data.index[-2])

        if self.force_close_date and current_date == self.force_close_date:
            print(f"Force closing all positions on {current_date}")
            self.position.close()
            return # Don't buy on the same day we are trying to exit

        if current_date.month != previous_date.month:
            self.buy_signal()
        
    def buy_signal(self):
        price = self.data.Close[-1]
        size_in_shares = math.floor(self.monthly_contribution / price)

        print(size_in_shares)
        print(self.equity)

        if size_in_shares >= 1:
            if self.equity >= (size_in_shares * price):
                size_in_shares = int(size_in_shares)
                self.buy(size = size_in_shares)
            else:
                print(f"Skipped DCA: Not enough cash to buy {size_in_shares} shares.")
