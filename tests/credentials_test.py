# import sys
# import os

# TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.dirname(TESTS_DIR)

# # Add Project Root to Python's search path
# sys.path.append(PROJECT_ROOT)

# --- START HERE ---
import config

print(f"API Key Loaded: {'Yes' if config.API_KEY else 'No'}")
print(f"API_KEY: {config.API_KEY}")





