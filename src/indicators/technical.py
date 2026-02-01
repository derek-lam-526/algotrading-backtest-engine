import pandas as pd
import numpy as np

def sma(series, period=20):
    return series.Close.rolling(14).mean()

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

def parabolic_sar(high, low, af_step=0.02, max_af=0.2):
    """
    Computes Parabolic SAR (Stop and Reverse).
    Returns: pd.Series
    """
    # Convert inputs to numpy arrays for speed
    high_arr = high.values
    low_arr = low.values
    length = len(high_arr)
    
    sar = np.zeros(length)
    
    # Initialize variables
    # We assume Uptrend at start
    is_uptrend = True
    ep = high_arr[0]      # Extreme Point (Highest High in Uptrend)
    sar[0] = low_arr[0]   # Starting SAR
    af = af_step          # Acceleration Factor
    
    for i in range(1, length):
        prev_sar = sar[i-1]
        
        # 1. Calculate new SAR based on yesterday's data
        if is_uptrend:
            sar[i] = prev_sar + af * (ep - prev_sar)
        else:
            sar[i] = prev_sar - af * (prev_sar - ep)
            
        # 2. Check for Reversal
        if is_uptrend:
            # If Low breaks below SAR -> Flip to Downtrend
            if low_arr[i] < sar[i]:
                is_uptrend = False
                sar[i] = ep          # SAR becomes the previous EP (Highest High)
                ep = low_arr[i]      # Reset EP to current low
                af = af_step         # Reset AF
            else:
                # Update EP if new high is made
                if high_arr[i] > ep:
                    ep = high_arr[i]
                    af = min(af + af_step, max_af)
                    
                # Constraint: SAR cannot be higher than previous 2 lows
                sar[i] = min(sar[i], low_arr[i-1])
                if i > 1:
                    sar[i] = min(sar[i], low_arr[i-2])
                    
        else: # Downtrend
            # If High breaks above SAR -> Flip to Uptrend
            if high_arr[i] > sar[i]:
                is_uptrend = True
                sar[i] = ep          # SAR becomes the previous EP (Lowest Low)
                ep = high_arr[i]     # Reset EP to current high
                af = af_step         # Reset AF
            else:
                # Update EP if new low is made
                if low_arr[i] < ep:
                    ep = low_arr[i]
                    af = min(af + af_step, max_af)
                    
                # Constraint: SAR cannot be lower than previous 2 highs
                sar[i] = max(sar[i], high_arr[i-1])
                if i > 1:
                    sar[i] = max(sar[i], high_arr[i-2])
                    
    return pd.Series(sar, index=high.index)

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
