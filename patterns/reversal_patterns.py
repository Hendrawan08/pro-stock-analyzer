import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from constants import REVERSAL_PATTERN_WINDOW

class ReversalPatterns:
    """
    Mendeteksi pola reversal Double Top dan Double Bottom.
    """

    def __init__(self, distance: int = REVERSAL_PATTERN_WINDOW, threshold: float = 0.03, reversal_factor: float = 0.05): # Menyesuaikan reversal factor
        """
        Inisialisasi parameter pola.
        :param distance: Jarak minimum (jumlah bar) antar puncak/lembah.
        :param threshold: Toleransi perbedaan harga antar puncak/lembah (misal: 0.03 = 3%).
        :param reversal_factor: Seberapa dalam 'lembah tengah' (DT) atau 'puncak tengah' (DB). 0.05 = 5%
        """
        self.distance = distance
        self.threshold = threshold
        self.reversal_factor = reversal_factor

    def detect_all(self, data: pd.DataFrame, interval: str) -> pd.DataFrame:
        """
        Menjalankan deteksi untuk Double Top dan Double Bottom.
        """
        # Pola ini tidak relevan untuk timeframe sangat pendek (intraday)
        if interval in ['1m', '5m', '15m']:
            data['DT_Signal'] = False
            data['DB_Signal'] = False
            return data

        data = self.detect_double_top(data)
        data = self.detect_double_bottom(data)
        return data

    def detect_double_top(self, data: pd.DataFrame) -> pd.DataFrame:
        """Mendeteksi pola Double Top (Pola 'M')"""
        data['DT_Signal'] = False
        
        peaks, _ = find_peaks(data['High'], distance=self.distance)
        
        if len(peaks) < 2:
            return data

        for i in range(len(peaks) - 1):
            p1_idx = peaks[i]
            p2_idx = peaks[i+1]
            
            p1_price = data['High'].iloc[p1_idx]
            p2_price = data['High'].iloc[p2_idx]

            if abs(p1_price - p2_price) / p1_price <= self.threshold:
                # 2. Cari lembah di antara dua puncak
                # --- PERBAIKAN: Gunakan .loc[] bukan .iloc[] ---
                valley_idx_label = data['Low'].iloc[p1_idx:p2_idx].idxmin() # Ini adalah Tanggal/Label
                valley_price = data['Low'].loc[valley_idx_label] # Gunakan .loc[]
                # -----------------------------------------------

                # 3. Cek apakah lembah cukup dalam (reversal)
                avg_peak_price = (p1_price + p2_price) / 2
                if (avg_peak_price - valley_price) / avg_peak_price > self.reversal_factor:
                    
                    # 4. Cek apakah harga saat ini (bar terakhir) menembus support lembah
                    current_price = data['Close'].iloc[-1]
                    if current_price < valley_price:
                        data.iloc[-1, data.columns.get_loc('DT_Signal')] = True
                        
        return data

    def detect_double_bottom(self, data: pd.DataFrame) -> pd.DataFrame:
        """Mendeteksi pola Double Bottom (Pola 'W')"""
        data['DB_Signal'] = False

        valleys, _ = find_peaks(-data['Low'], distance=self.distance)
        
        if len(valleys) < 2:
            return data

        for i in range(len(valleys) - 1):
            v1_idx = valleys[i]
            v2_idx = valleys[i+1]
            
            v1_price = data['Low'].iloc[v1_idx]
            v2_price = data['Low'].iloc[v2_idx]

            if abs(v1_price - v2_price) / v1_price <= self.threshold:
                # 2. Cari puncak di antara dua lembah
                # --- PERBAIKAN: Gunakan .loc[] bukan .iloc[] ---
                peak_idx_label = data['High'].iloc[v1_idx:v2_idx].idxmax() # Ini adalah Tanggal/Label
                peak_price = data['High'].loc[peak_idx_label] # Gunakan .loc[]
                # -----------------------------------------------

                # 3. Cek apakah puncak tengah cukup tinggi (reversal)
                avg_valley_price = (v1_price + v2_price) / 2
                if (peak_price - avg_valley_price) / avg_valley_price > self.reversal_factor:
                    
                    # 4. Cek apakah harga saat ini (bar terakhir) menembus resistance puncak
                    current_price = data['Close'].iloc[-1]
                    if current_price > peak_price:
                        data.iloc[-1, data.columns.get_loc('DB_Signal')] = True
                        
        return data