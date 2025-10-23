# indicators/bollinger_bands.py
from indicators.base_indicator import BaseIndicator
import pandas as pd
import ta
from constants import BB_WINDOW

class BollingerBands(BaseIndicator):
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Menambahkan Bollinger Bands ke DataFrame."""
        bb = ta.volatility.BollingerBands(
            data["Close"], window=BB_WINDOW, window_dev=2, fillna=False
        )
        data["BB_Upper"] = bb.bollinger_hband()
        data["BB_Middle"] = bb.bollinger_mavg()
        data["BB_Lower"] = bb.bollinger_lband()
        return data