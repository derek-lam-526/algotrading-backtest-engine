from datetime import datetime 
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import strategies

# --- MODE SELECTION ---
# Options: "SINGLE" (Runs one specific ticker) 
#          "BATCH"  (Runs the full list below)

RUN_MODE = "SINGLE"

# --- SYMBOL CHOICE ---
SINGLE_SYMBOL = "SPY"
BATCH_SYMBOLS = [
    "AAPL", "NVDA", "TSLA", "MSFT", "AMD", 
    "META", "AMZN", "GOOGL", "KO", "SPY"
]

# --- DATES & TIMEFRAME ---
START_DATE = datetime(2022, 12, 1)
END_DATE   = datetime(2026, 1, 1)

TIMEFRAME  = TimeFrame(1, TimeFrameUnit.Hour) # Minute, Hour, Day, Week, Month

# --- ACCOUNT SETTINGS ---
INITIAL_CASH = 50_000
COMMISSION   = (0.35, 0.001)  # (Minimum $0.35 per trade, or 0.1% volume)

# --- STRATEGY ---
ACTIVE_STRATEGY = strategies.LrcReversion

# --- STRATEGY PARAMETERS ---
# These override the default values inside your Strategy Class.
STRATEGY_PARAMS = {
    "lrc_window": 60,
    "slope_threshold": 8
}

