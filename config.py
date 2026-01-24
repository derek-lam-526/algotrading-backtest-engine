import os

# Alpaca API CREDENTIALS
API_KEY = "PKQHQDBXXJS7OCYX5PWSAXV3TX"
SECRET_KEY = "7mAQkxwsCfbKcS7SxZ1RYxAhczJrUjvqMFQsYECxDd1t"


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")

# Automatically create folders when this file is imported
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
