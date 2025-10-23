# indicators/macd.py
from indicators.base_indicator import BaseIndicator
import pandas as pd
import ta

class MACD(BaseIndicator):
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Menambahkan MACD dan Signal Line ke DataFrame."""
        macd_indicator = ta.trend.MACD(data["Close"], fillna=False)
        data["MACD"] = macd_indicator.macd()
        data["MACD_Signal"] = macd_indicator.macd_signal()
        data["MACD_Hist"] = macd_indicator.macd_diff()
        return data