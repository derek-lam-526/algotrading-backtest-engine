import pandas_ta as ta
import pandas as pd 
import numpy as np 
from typing import List, Dict, Optional

class FeatureEngineer:
    def __init__(self, config: Dict = None):
        self.config = config if config else self._dafault_config()
    
    def _default_config(self):
        return {
            "volume_filter": True,
            "indicators":[
                {"kind": "rsi", "length": 14},
                {"kind": "bbands", "length": 20},
                {"kind": "macd", "fast": 12, "slow": 26},
            ]
        }

    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if self.config.get("volume_filter"):
            df = df[df['Volume'] > 0]
        
        CustomStrategy = ta.Strategy(
            name = "MyStrategy",
            ta=self.config["indicators"]
        )

        df.ta.strategy(CustomStrategy)
