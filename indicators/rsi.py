# indicators/rsi.py
from indicators.base_indicator import BaseIndicator
import pandas as pd
import ta
from constants import RSI_WINDOW

class RSI(BaseIndicator):
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Menambahkan Relative Strength Index (RSI) ke DataFrame."""
        data["RSI"] = ta.momentum.RSIIndicator(data["Close"], window=RSI_WINDOW, fillna=False).rsi()
        return data