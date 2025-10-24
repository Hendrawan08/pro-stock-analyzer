# patterns/reversal_patterns.py
import pandas as pd
import numpy as np
from constants import PATTERN_DISTANCE, PATTERN_THRESHOLD, PATTERN_REVERSAL_FACTOR

class ReversalPatterns:
    
    def detect_all(self, data: pd.DataFrame, interval: str) -> pd.DataFrame:
        """
        Mendeteksi pola Double Top dan Double Bottom dengan logika yang diperbaiki
        dan parameter DINAMIS (lebih sensitif) berdasarkan interval.
        """
        
        # --- Inisialisasi Kolom ---
        data["DB_Signal"] = False
        data["DT_Signal"] = False
        data["Engulfing_B"] = False 
        data["Engulfing_S"] = False
        
        close_values = data["Close"].values
        n = len(close_values)
        
        # ==========================================================
        # LOGIKA PARAMETER DINAMIS (PINTAR)
        # ==========================================================
        if interval == "1m":
            # Paling sensitif untuk 1 Menit
            distance = 240          # 4 jam trading (240 bar)
            threshold = 0.0025      # 0.25% (sebelumnya 0.5%)
            reversal_factor = 0.004 # 0.4% (sebelumnya 0.7%)
        elif interval == "15m":
            # Sensitif untuk 15 Menit
            distance = 80           # ~5 hari
            threshold = 0.005       # 0.5%
            reversal_factor = 0.007 # 0.7%
        elif interval == "1h":
            # Sensitif untuk 1 Jam
            distance = 60           # ~10 hari
            threshold = 0.005       # 0.5%
            reversal_factor = 0.007 # 0.7%
        else: 
            # Parameter Harian/Mingguan (mengambil dari constants.py)
            distance = PATTERN_DISTANCE 
            threshold = PATTERN_THRESHOLD
            reversal_factor = PATTERN_REVERSAL_FACTOR
        # ==========================================================

        # Pastikan data cukup panjang untuk memiliki 'left_area'
        if n < (distance + 1):
            return data

        # Kita iterasi dari 'distance' agar selalu punya 'left_area'
        for i in range(distance, n):
            
            current_price = close_values[i]
            # 'left_area' adalah jendela untuk mencari pola PERTAMA
            left_area = close_values[i - distance : i] 

            # --- Logika Baru: Double Bottom (Bentuk 'W') ---
            if left_area.size > 0:
                bottom_1 = np.min(left_area) 
                neckline = np.max(left_area) 
                bottom_2 = current_price     

                # Gunakan parameter dinamis
                is_similar = abs(bottom_1 - bottom_2) / bottom_1 < threshold
                has_reversal = (neckline > bottom_1 * (1 + reversal_factor)) and \
                               (neckline > bottom_2 * (1 + reversal_factor))
                is_local_min = current_price <= np.min(close_values[max(0, i-2):i+1])

                if is_similar and has_reversal and is_local_min:
                    data.loc[data.index[i], "DB_Signal"] = True


            # --- Logika Baru: Double Top (Bentuk 'M') ---
            if left_area.size > 0:
                top_1 = np.max(left_area)  
                trough = np.min(left_area) 
                top_2 = current_price      

                # Gunakan parameter dinamis
                is_similar_top = abs(top_1 - top_2) / top_1 < threshold
                has_reversal_top = (trough < top_1 * (1 - reversal_factor)) and \
                                   (trough < top_2 * (1 - reversal_factor))
                is_local_max = current_price >= np.max(close_values[max(0, i-2):i+1])

                if is_similar_top and has_reversal_top and is_local_max:
                    data.loc[data.index[i], "DT_Signal"] = True
                        
        return data # <-- PERBAIKAN: Menghapus tanda kurung ')' ekstra