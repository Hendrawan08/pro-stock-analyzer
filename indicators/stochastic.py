import pandas as pd
import ta
# --- PERBAIKAN: Impor konstanta yang benar ---
from constants import STOCHASTIC_K, STOCHASTIC_D, STOCHASTIC_SMOOTH_K
# ---------------------------------------------

class Stochastic:
    """
    Menghitung Stochastic Oscillator (%K dan %D).
    """

    # --- PERBAIKAN: Gunakan konstanta yang benar di __init__ ---
    def __init__(self, k: int = STOCHASTIC_K, d: int = STOCHASTIC_D, smooth_k: int = STOCHASTIC_SMOOTH_K):
    # --------------------------------------------------------
        self.k = k
        self.d = d
        self.smooth_k = smooth_k

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Menghitung dan menambahkan kolom Stochastic (%K dan %D) ke DataFrame.
        """
        if self.k > 0 and self.k < len(data):
            # Menggunakan library ta untuk perhitungan
            indicator = ta.momentum.StochasticOscillator(
                high=data['High'], 
                low=data['Low'], 
                close=data['Close'], 
                window=self.k, 
                smooth_window=self.d, # Perhatikan: di 'ta', smooth_window adalah %D
                fillna=True
            )
            data['%K'] = indicator.stoch()      # Ini adalah %K
            data['%D'] = indicator.stoch_signal() # Ini adalah %D (sinyal dari %K)
        else:
            # Fallback jika data tidak cukup
            data['%K'] = 50.0 # Default ke 50 (Netral)
            data['%D'] = 50.0 # Default ke 50 (Netral)
            
        return data