import pandas as pd
# --- PERBAIKAN: Impor konstanta individual ---
from constants import MA_SHORT_WINDOW, MA_MEDIUM_WINDOW, MA_LONG_WINDOW
# ---------------------------------------------

class MovingAverage:
    """
    Menghitung Moving Averages (MA) sederhana.
    """
    
    # --- PERBAIKAN: Gunakan konstanta individual ---
    # Buat dictionary config DI DALAM class
    MA_CONFIG = {
        'MA_S': MA_SHORT_WINDOW,
        'MA_M': MA_MEDIUM_WINDOW,
        'MA_L': MA_LONG_WINDOW
    }
    # -----------------------------------------------

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Menghitung dan menambahkan kolom MA ke DataFrame.
        """
        for key, window in self.MA_CONFIG.items():
            if window > 0 and window <= len(data):
                data[key] = data['Close'].rolling(window=window).mean().fillna(data['Close'])
            elif window > len(data):
                # Jika data lebih pendek dari window, gunakan rata-rata semua data
                data[key] = data['Close'].mean() 
            else:
                # Fallback jika window = 0 atau negatif (seharusnya tidak terjadi)
                data[key] = data['Close']
                
        return data