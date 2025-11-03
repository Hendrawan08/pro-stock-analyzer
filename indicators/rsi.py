import pandas as pd
import ta
# --- PERBAIKAN: Impor konstanta yang benar ---
from constants import RSI_PERIOD
# ---------------------------------------------

class RSI:
    """
    Menghitung Relative Strength Index (RSI).
    """

    # --- PERBAIKAN: Gunakan konstanta yang benar ---
    def __init__(self, window: int = RSI_PERIOD):
    # ---------------------------------------------
        self.window = window

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Menghitung dan menambahkan kolom RSI ke DataFrame.
        """
        if self.window > 0 and self.window < len(data):
            # Menggunakan library ta untuk perhitungan RSI yang akurat
            data['RSI'] = ta.momentum.RSIIndicator(
                close=data['Close'], 
                window=self.window, 
                fillna=True
            ).rsi()
        else:
            # Fallback jika data tidak cukup atau window 0
            data['RSI'] = 50.0  # Default ke 50 (Netral)
            
        return data