def validate_dataframe(df):
    """Ensures Dataframe has required columns for Backtesting."""
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing = [col for col in required if col not in df.columns]
    
    if missing:
        raise ValueError(f"Dataframe is missing required columns: {missing}")
    
    if df.empty:
        raise ValueError("Dataframe is empty.")
    return True
