import pandas as pd
import ta
# --- PERBAIKAN: Impor konstanta yang benar ---
from constants import BOLLINGER_WINDOW, BOLLINGER_STD
# ---------------------------------------------

class BollingerBands:
    """
    Menghitung Bollinger Bands (BB).
    """

    # --- PERBAIKAN: Gunakan konstanta yang benar di __init__ ---
    def __init__(self, window: int = BOLLINGER_WINDOW, std: int = BOLLINGER_STD):
    # --------------------------------------------------------
        self.window = window
        self.std = std

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Menghitung dan menambahkan kolom Bollinger Bands ke DataFrame.
        """
        if self.window > 0 and self.window < len(data):
            # Menggunakan library ta untuk perhitungan
            indicator = ta.volatility.BollingerBands(
                close=data['Close'], 
                window=self.window, 
                window_dev=self.std, 
                fillna=True
            )
            data['BB_High'] = indicator.bollinger_hband() # High Band
            data['BB_Low'] = indicator.bollinger_lband()  # Low Band
            data['BB_Mid'] = indicator.bollinger_mavg()  # Middle Band (MA)
        else:
            # Fallback jika data tidak cukup
            data['BB_High'] = data['Close']
            data['BB_Low'] = data['Close']
            data['BB_Mid'] = data['Close']
            
        return data