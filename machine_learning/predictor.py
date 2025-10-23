# machine_learning/predictor.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import streamlit as st
import joblib # Perlu untuk save/load model
import os # Perlu untuk mengecek apakah file ada

# --- Import semua yang dibutuhkan untuk PELATIHAN ---
# Ini diperlukan agar kita bisa melatih model di dalam file ini
from data.data_manager import DataManager
from indicators.moving_average import MovingAverage
from indicators.rsi import RSI
from indicators.macd import MACD
from indicators.bollinger_bands import BollingerBands
from indicators.stochastic import Stochastic
# (Kita tidak perlu ReversalPatterns untuk fitur ML)

MODEL_PATH = 'machine_learning/saved_model.joblib'
ACCURACY_PATH = 'machine_learning/model_accuracy.txt'
FEATURES = ['RSI', 'MACD', 'MACD_Signal', 'MA_S', 'MA_L', 'BB_Upper', 'BB_Lower', '%K', '%D'] # Menambahkan %K dan %D

# Fungsi ini akan melatih model DARI AWAL
# Ini akan dipanggil HANYA JIKA file model tidak ada
def _train_new_model():
    """Melatih model baru dari data 10 tahun ^JKSE dan menyimpannya."""
    st.info("Membuat model Machine Learning baru. Ini hanya berjalan sekali dan mungkin perlu waktu...")
    
    # 1. Ambil data 10 TAHUN untuk pelatihan (menggunakan ^JKSE sebagai proxy)
    data_manager = DataManager(None, None, None)
    # Ambil data 10 tahun, interval 1 hari
    train_data = data_manager.fetch_data("^JKSE", "10y", "1d")
    
    if train_data is None:
        st.error("Gagal mengambil data pelatihan untuk ML. Model tidak akan bekerja.")
        return None, 0.0

    # 2. Hitung semua indikator untuk data pelatihan
    train_data = MovingAverage().calculate(train_data)
    train_data = RSI().calculate(train_data)
    train_data = MACD().calculate(train_data)
    train_data = BollingerBands().calculate(train_data)
    train_data = Stochastic().calculate(train_data)
    
    # 3. Siapkan Fitur (X) dan Target (y)
    df = train_data.copy().dropna()
    # Target: Harga Close besok lebih tinggi dari harga Close hari ini
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True) # Hapus baris terakhir (Target=NaN)

    X = df[FEATURES]
    y = df['Target']

    # 4. Latih Model
    # Kita pakai 80% data untuk train, 20% untuk test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    if len(X_train) < 100:
         st.error("Data pelatihan tidak cukup setelah diproses. Model ML gagal.")
         return None, 0.0

    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 5. Evaluasi dan simpan akurasi
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # 6. Simpan model ke file
    joblib.dump(model, MODEL_PATH)
    # Simpan akurasi juga agar tidak perlu dihitung ulang
    with open(ACCURACY_PATH, 'w') as f:
        f.write(str(accuracy))
    
    st.success(f"Model ML baru berhasil dibuat! (Akurasi: {accuracy*100:.1f}%)")
    
    return model, accuracy

# Gunakan cache_resource untuk memuat model HANYA SEKALI saat app start
@st.cache_resource
def load_model_and_accuracy():
    """
    Memuat model dari file. Jika file tidak ada,
    fungsi _train_new_model akan dipanggil.
    """
    if not os.path.exists(MODEL_PATH):
        # File model tidak ada, latih yang baru
        model, accuracy = _train_new_model()
    else:
        # File model SUDAH ADA, tinggal load
        model = joblib.load(MODEL_PATH)
        # Load akurasi dari file
        try:
            with open(ACCURACY_PATH, 'r') as f:
                accuracy = float(f.read())
        except FileNotFoundError:
            # Jika file akurasi terhapus, kita latih ulang saja
            st.warning("File akurasi tidak ditemukan. Melatih ulang model...")
            model, accuracy = _train_new_model()

    return model, accuracy


class MLPredictor:
    """
    Versi BARU: Memuat model yang sudah ada, tidak melatih ulang.
    """
    
    def __init__(self):
        # Saat kelas diinisialisasi, panggil fungsi cache untuk memuat model
        self.model, self.accuracy = load_model_and_accuracy()

    def predict(self, data: pd.DataFrame) -> tuple[float, str]:
        """
        Fungsi BARU: Hanya untuk PREDIKSI.
        Tidak ada lagi pelatihan di sini.
        """
        
        if self.model is None:
            return 0.0, "Model ML tidak ter-load."

        # Ambil data baris TERAKHIR dari data yang sudah dianalisis
        # Pastikan semua fitur ada
        try:
            last_features_df = data.iloc[-1:]
            X_pred = last_features_df[FEATURES]
        except KeyError as e:
            st.error(f"Error fitur ML: Kolom {e} tidak ditemukan. Model mungkin tidak akurat.")
            return self.accuracy, "Error"
        except Exception as e:
            st.error(f"Error saat menyiapkan data prediksi ML: {e}")
            return self.accuracy, "Error"

        # Prediksi Hari Berikutnya
        prediction = self.model.predict(X_pred)[0]

        pred_str = "NAIK (BUY)" if prediction == 1 else "TURUN (SELL)"
        
        # Kembalikan akurasi yang sudah tersimpan
        return self.accuracy, pred_str