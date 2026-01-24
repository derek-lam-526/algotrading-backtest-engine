import pandas as pd
import numpy as np

def rsi(series, period=14):
    """
    Computes the Relative Strength Index (RSI).
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def bollinger_bands(series, period=20, std_dev=2):
    """
    Computes Bollinger Bands.
    Returns: (Upper, Middle, Lower)
    """
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower

def macd(series, fast=12, slow=26, signal=9):
    """
    Computes MACD (Moving Average Convergence Divergence).
    Returns: (MACD_Line, Signal_Line, Histogram)
    """
    # 1. Calculate Fast and Slow EMAs
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()

    # 2. Calculate MACD Line
    macd_line = ema_fast - ema_slow

    # 3. Calculate Signal Line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    # 4. Calculate Histogram (Optional, but useful for visuals)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram
