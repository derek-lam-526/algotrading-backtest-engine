# src/strategies/base.py
from backtesting import Strategy

class BaseStrategy(Strategy):
    """
    Parent class for all strategies.
    Handles global checks or logging.
    """
    
    def init(self):
        # You can initialize shared indicators here if needed
        pass

    def log(self, message):
        """Helper to print with timestamp"""
        print(f"[{self.data.index[-1]}] {message}")
