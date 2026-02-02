import numpy as np
import pandas as pd
from strategies.base import BaseStrategy
from backtesting.lib import crossover

def rolling_lrc_metrics(close, window=10, num_std=2, days_per_year=252):
    y = pd.Series(close)
    x = pd.Series(np.arange(len(y)))

    rolling_y = y.rolling(window=window)

    cov_xy = y.rolling(window=window).cov(x)
    var_x = x.rolling(window=window).var()
    slope = cov_xy / var_x

    mean_y = rolling_y.mean()
    mean_x = x.rolling(window=window).mean()
    intercept = mean_y - (slope * mean_x)

    center_line = (slope * x) + intercept 

    corr_xy = rolling_y.corr(x)
    r_squared = corr_xy ** 2
    std_y = rolling_y.std()

    n = window
    see = std_y * np.sqrt(1 - r_squared) * np.sqrt((n-1) / (n-2))

    upper = center_line + (num_std * see)
    lower = center_line - (num_std * see)

    slope_pct = (slope / center_line) * days_per_year * 100 

    width_pct = (upper - lower) / center_line

    width_rank = width_pct.rolling(200).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=True)

    return (center_line.values,
            upper.values,
            lower.values,
            slope_pct.values,
            r_squared.values,
            width_rank.values)

class LrcReversion(BaseStrategy):
    """
    Linear Regression Channel (LRC) Mean Reversion Strategy.
    
    This strategy attempts to capture mean-reversion moves when price extends beyond 
    statistical bounds (Standard Deviations) of a rolling Linear Regression Channel.
    It includes filters to avoid catching falling knives during strong trends or 
    entering during volatility squeezes.

    PARAMETERS
    ----------
    lrc_window : int (Default: 40)
        The lookback period for calculating the Linear Regression Channel.
        
    n_std : float (Default: 2)
        The width of the channel bands in Standard Deviations (adjusted for SEE).
        
    slope_threshold : float (Default: 15)
        Filter: The maximum allowed annualized slope %. If the channel is steeping 
        down faster than this, Long entries are blocked (avoids strong trends).
        
    r2_threshold : float (Default: 0.4)
        Filter: The minimum R-Squared (0-1) required to activate the Slope Filter.
        If R2 is high, the trend is "smooth/strong", so we respect the Slope block.
        
    squeeze_percentile : float (Default: 0.2)
        Filter: Avoid entries if the Channel Width is in the bottom 20% of its
        history (indicates a 'Squeeze' where explosive breakouts often occur).
        
    stop_loss_pct : float (Default: 0.05)
        Hard Stop Loss distance (0.05 = 5%).

    LOGIC
    -----
    1. ENTRY (Long): 
       - Price crosses below the Lower LRC Band.
       - FILTER 1 (Anti-Knife): Entry is rejected if Slope < -slope_threshold 
         AND R2 > r2_threshold (Signal: Trend is too strong to fade).
       - FILTER 2 (Squeeze): Entry is rejected if width is in bottom percentile.
    
    2. EXIT: 
       - Take Profit: Price reverts to the midpoint (Average of Center & Upper Band).
       - Stop Loss: Fixed % from entry price.
    """
    
    lrc_window = 40
    n_std = 2
    slope_threshold = 15
    r2_threshold = 0.4
    squeeze_percentile = 0.2
    stop_loss_pct = 0.05
    
    def init(self):
        super().init()

        metrics = rolling_lrc_metrics(close=self.data.Close, 
                                      window=self.lrc_window,
                                      num_std=self.n_std,
                                      days_per_year=252)
        
        self.center = self.I(lambda: metrics[0], 
                             name="LRC_Center",
                             overlay=True,
                             color="pink")
        
        self.upper = self.I(lambda: metrics[1],
                            name="LRC_Upper",
                            overlay=True,
                            color="purple")
        
        self.lower = self.I(lambda: metrics[2],
                            name="LRC_Lower",
                            overlay=True,
                            color="yellow")
        
        self.slope_pct = self.I(lambda: metrics[3],
                                name="Slope%",
                                overlay=False,
                                color="orange")
        
        self.r2= self.I(lambda: metrics[4],
                        name="R2",
                        overlay=False,
                        color="blue")
        
        self.width_rank = self.I(lambda: metrics[5],
                                 name="Width_Rank",
                                 overlay=False,
                                 color="purple")
        
    def next(self):
        price = self.data.Close[-1]

        # Filter squeeze cases
        if self.width_rank[-1] < self.squeeze_percentile:
            return 
        
        # Long Entry
        if price < self.lower[-1]:
            is_strong_bear = (self.slope_pct[-1] < -self.slope_threshold)
            is_smooth_trend = (self.r2[-1] > self.r2_threshold)

            if is_strong_bear and is_smooth_trend:
                pass
            else: 
                if not self.position.is_long:
                    self.buy(sl = price * (1 - self.stop_loss_pct))

        # Short Entry
        # if price > self.upper[-1]:
        #     is_strong_bull = (self.slope_pct[-1] > self.slope_threshold)
        #     is_smooth_trend = (self.r2[-1] > self.r2_threshold)

        #     if is_strong_bull and is_smooth_trend:
        #         pass 
        #     else:
        #         if not self.position.is_short:
        #             self.sell(sl = price * (1 + self.stop_loss_pct))
        
        # Exit Logic
        if self.position.is_long and price >= (self.center[-1] + self.upper[-1]) / 2:
            self.position.close()
        if self.position.is_short and price <= (self.center[-1] + self.lower[-1]) / 2:
            self.position.close()
