# indicators/stochastic.py
from indicators.base_indicator import BaseIndicator
import pandas as pd
import ta
from constants import STOCH_K, STOCH_D

class Stochastic(BaseIndicator):
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Menambahkan Stochastic Oscillator (%K dan %D) ke DataFrame."""
        stoch = ta.momentum.StochasticOscillator(
            data["High"], data["Low"], data["Close"], window=STOCH_K, smooth_window=STOCH_D, fillna=False
        )
        # GANTI NAMA KOLOM DI SINI:
        data["%K"] = stoch.stoch()           # Menggunakan '%K'
        data["%D"] = stoch.stoch_signal()    # Menggunakan '%D'
        # ==========================
        return data