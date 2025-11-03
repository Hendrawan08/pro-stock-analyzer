# indicators/macd.py
import pandas as pd
import ta
from constants import MACD_FAST, MACD_SLOW, MACD_SIGNAL

class MACD:
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Menambahkan MACD dan Signal Line ke DataFrame."""
        macd_indicator = ta.trend.MACD(
            data["Close"], 
            window_fast=MACD_FAST,
            window_slow=MACD_SLOW,
            window_sign=MACD_SIGNAL,
            fillna=False
        )
        data["MACD"] = macd_indicator.macd()
        data["MACD_Signal"] = macd_indicator.macd_signal()
        data["MACD_Hist"] = macd_indicator.macd_diff()

        # PERBAIKAN V7.2: Isi NaN di awal dengan 0
        data["MACD"] = data["MACD"].fillna(0)
        data["MACD_Signal"] = data["MACD_Signal"].fillna(0)
        data["MACD_Hist"] = data["MACD_Hist"].fillna(0)
        
        return data