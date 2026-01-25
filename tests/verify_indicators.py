import sys
import os

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)

# Add Project Root to Python's search path
sys.path.append(PROJECT_ROOT)

# --- START HERE ---
import pandas as pd 
from datetime import datetime
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit 

from src.config import API_KEY, SECRET_KEY, OUTPUT_DIR
from src.core import DataManager 
import src.indicators as Indicators


def verify_indicators():
    dm = DataManager(API_KEY, SECRET_KEY)
    symbol = "SPY"

    end = datetime(2026,1,24)
    start = datetime(2024,1,1)

    df = dm.get_data(symbol, start, end, timeframe=TimeFrame.Day)

    print(f"Loaded {len(df)} rows for {symbol}...")

    df["RSI"] = Indicators.rsi(df["Close"], 14)

    upper, mid, lower = Indicators.bollinger_bands(df["Close"], 20, 2)
    df["BB_Upper"] = upper
    df["BB_Mid"] = mid 
    df["BB_Lower"] = lower 

    macd, signal, hist = Indicators.macd(df["Close"], 12, 26, 9)

    df["MACD_Line"] = macd 
    df["MACD_Signal"] = signal 
    df["MACD_Hist"] = hist 

    sar = Indicators.parabolic_sar(df["High"], df["Low"], 0.02, 0.2)

    df["SAR"] = sar 

    cols_to_check = ['Close', 'RSI', 'BB_Upper', 'BB_Mid', 'BB_Lower', 'MACD_Line', 'MACD_Signal', 'MACD_Hist', "SAR"]
    output = df[cols_to_check].tail(10).round(3)

    print("\n--- COMPARISON TABLE (Last 10 Candles) ---")
    print(output)

    csv_name = f"{OUTPUT_DIR}/verify_data.csv"
    output.to_csv(csv_name)
    print(f"\nSaved full data to {csv_name}.")

if __name__ == "__main__":
    verify_indicators()
