import pandas as pd
from constants import MA_CONFIG

class MovingAverage:
    
    def __init__(self, short: int = MA_CONFIG['short'], 
                 medium: int = MA_CONFIG['medium'], 
                 long: int = MA_CONFIG['long']):
        """
        Inisialisasi dengan periode MA yang dapat dikonfigurasi.
        """
        self.short = short
        self.medium = medium
        self.long = long

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Menghitung Moving Average Sederhana (SMA) untuk periode pendek, menengah, dan panjang.
        Jika data terlalu pendek, kolom MA akan diisi NaN.
        """
        
        # Daftar kolom MA yang harus dihitung
        ma_periods = {
            'MA_S': self.short, 
            'MA_M': self.medium, 
            'MA_L': self.long
        }
        
        # Hitung MA hanya jika data cukup panjang
        for col_name, period in ma_periods.items():
            if len(data) >= period:
                data[col_name] = data['Close'].rolling(window=period).mean()
            else:
                # Jika data tidak cukup, isi dengan NaN agar tidak error
                # Ini akan membuat aplikasi tetap berjalan
                data[col_name] = pd.NA 
        
        return data
