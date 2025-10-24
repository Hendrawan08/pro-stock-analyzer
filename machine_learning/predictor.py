# machine_learning/predictor.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import streamlit as st
# HAPUS: joblib, os, dan semua impor indikator (tidak diperlukan lagi)

# Fitur tetap sama, karena analyzer.py sudah menyiapkannya
FEATURES = ['RSI', 'MACD', 'MACD_Signal', 'MA_S', 'MA_L', 'BB_Upper', 'BB_Lower', '%K', '%D'] 

# ==========================================================
# FUNGSI BARU V2.1: PELATIHAN DINAMIS PER SAHAM
# ==========================================================
@st.cache_data(show_spinner=False)
def _train_model_dynamically(data: pd.DataFrame) -> tuple[RandomForestClassifier | None, float]:
    """
    Melatih model baru secara dinamis HANYA PADA DATA SAHAM INI.
    Hasilnya (model & akurasi) akan di-cache oleh Streamlit.
    Fungsi ini akan dipanggil oleh MLPredictor.
    """
    try:
        # 1. Siapkan Fitur (X) dan Target (y)
        # Kita gunakan data yang sudah dihitung indikatornya
        df = data.copy().dropna(subset=FEATURES) 
        
        # Target: Harga Close besok lebih tinggi dari harga Close hari ini
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        df.dropna(inplace=True) # Hapus baris terakhir (Target=NaN)

        if df.empty:
            return None, 0.0

        X = df[FEATURES]
        y = df['Target']

        # 2. Latih Model
        # Kita pakai 80% data untuk train, 20% untuk test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        if len(X_train) < 50: # Butuh data yang cukup
            print(f"Peringatan ML: Data pelatihan terlalu sedikit ({len(X_train)} baris).")
            return None, 0.0

        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)

        # 3. Evaluasi dan dapatkan akurasi
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        return model, accuracy
        
    except Exception as e:
        print(f"Error saat melatih ML: {e}") # Log ke console, jangan ke UI
        return None, 0.0


# ==========================================================
# KELAS PREDICTOR BARU (LEBIH SEDERHANA)
# ==========================================================
class MLPredictor:
    """
    Versi BARU (V2.1):
    Melatih model secara dinamis untuk SETIAP saham.
    Tidak ada lagi cache file global.
    """
    
    def __init__(self):
        # Kosong, tidak ada model yang di-load
        pass

    def predict(self, data: pd.DataFrame) -> tuple[float, str]:
        """
        Fungsi BARU: 
        1. Memanggil fungsi training yang di-cache (_train_model_dynamically).
        2. Melakukan prediksi pada baris terakhir.
        """
        
        # 1. Dapatkan model & akurasi (akan di-cache per saham)
        # Ini akan instan jika 'data' tidak berubah (karena cache di app.py)
        model, accuracy = _train_model_dynamically(data)
        
        if model is None:
            return accuracy, "Data N/A" # 'accuracy' akan 0.0

        # 2. Ambil data baris TERAKHIR untuk prediksi
        try:
            last_features_df = data.iloc[-1:]
            
            # Cek jika ada NaN di baris terakhir (bisa terjadi di data live)
            if last_features_df[FEATURES].isnull().values.any():
                return accuracy, "Data N/A"
                
            X_pred = last_features_df[FEATURES]
        
        except KeyError as e:
            print(f"Error fitur ML: Kolom {e} tidak ditemukan.")
            return accuracy, "Error"
        except Exception as e:
            print(f"Error saat menyiapkan data prediksi ML: {e}")
            return accuracy, "Error"

        # 3. Prediksi Hari Berikutnya
        prediction = model.predict(X_pred)[0]
        pred_str = "NAIK (BUY)" if prediction == 1 else "TURUN (SELL)"
        
        # Kembalikan akurasi DINAMIS yang baru dihitung
        return accuracy, pred_str
