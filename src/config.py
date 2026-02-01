import os
from dotenv import load_dotenv

SRC_DIR = os.path.dirname(os.path.abspath(__file__)) 
PROJECT_ROOT = os.path.dirname(SRC_DIR) 
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PARQUET_DIR = os.path.join(DATA_DIR, "parquet")
CSV_DIR = os.path.join(DATA_DIR, "csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# Alpaca API CREDENTIALS
load_dotenv(DOTENV_PATH)
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

# Validation of API CREDENTIALS
if not API_KEY or not SECRET_KEY:
    raise ValueError("Error: API Keys not found. Did you create the .env file?")

# Automatically create folders when this file is imported
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PARQUET_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True) 
