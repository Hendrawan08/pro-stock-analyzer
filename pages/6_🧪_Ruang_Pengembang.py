# pages/6_🧪_Ruang_Pengembang.py (Versi diperkuat: try/except di seluruh bagian)
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
from prophet import Prophet
import time
import sys, os

# --- PENTING: Impor dari root folder ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ----------------------------------------

try:
    # Kita masih pakai MLPredictor, tapi sebagai sinyal sekunder
    from machine_learning.predictor import MLPredictor
    from constants import *
except Exception as e:
    # Jangan stop di sini agar halaman admin masih bisa terbuka untuk debugging,
    # namun beri peringatan kalau modul ML tidak tersedia.
    st.warning(f"Imports warning: {e}")
    MLPredictor = None

# ==========================================================
# GANTI PASSWORD ANDA DI SINI
# ==========================================================
# Ambil password dari Streamlit secrets, fallback ke env var atau default (untuk dev)
ADMIN_PASSWORD = None
try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except Exception:
    # fallback dev (jika belum diset di Cloud) — *jangan* commit produksi password
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# ==========================================================

st.set_page_config(
    page_title="Ruang Pengembang",
    page_icon="🧪",
    layout="wide"
)

# ==========================================================
# FUNGSI HELPER (Tetap Sama tapi tahan error)
# ==========================================================
def _normalize_ticker(ticker: str) -> str:
    """Memastikan ticker dalam format uppercase dan diakhiri .JK"""
    try:
        ticker = str(ticker).upper().strip()
        if ticker and not ticker.endswith(".JK") and '.' not in ticker:
            ticker += ".JK"
        return ticker
    except Exception:
        return ticker

def _round_price(price, base=5):
    """Membulatkan harga ke kelipatan 'base' terdekat."""
    try:
        price = float(price)
    except Exception:
        return price
    if price < 500:
        base = 1
    elif price < 2000:
        base = 5
    elif price < 5000:
        base = 10
    else:
        base = 25
    return base * round(price / base)

def _parse_ml_direction(ml_pred_str: str) -> int:
    """Mengubah string prediksi ML menjadi 1 (Naik), -1 (Turun), or 0 (Netral)."""
    try:
        ms = str(ml_pred_str).upper()
        if ("NAIK" in ms) or ("BUY" in ms):
            return 1
        elif ("TURUN" in ms) or ("SELL" in ms):
            return -1
        else:
            return 0
    except Exception:
        return 0

def safe_get(row, col, default=None):
    """Akses kolom dari Series/DataFrame row secara aman."""
    try:
        if col in row.index:
            return row[col]
        # kadang nama indikator kecil/besar berbeda, coba lowercase match
        for c in row.index:
            if str(c).lower() == str(col).lower():
                return row[c]
    except Exception:
        pass
    return default

# ==========================================================
# FUNGSI ANALISIS BARU (Overnight Strategy - Diperkuat)
# ==========================================================
def get_overnight_recommendation(ticker: str, ml_conf_threshold_local: float = 0.5, debug_local: bool = False):
    """
    Menganalisis ticker menggunakan data intraday (1h) untuk strategi
    beli sore - jual besok.
    Semua langkah dibungkus try/except supaya tidak memecah screener massal.
    """

    out = {
        "ticker": ticker,
        "current_price": None,
        "buy_rec": None,
        "take_profit": None,
        "stop_loss": None,
        "status": "Error",
        "signal_source": "N/A",
        "rr_rating": "N/A",
        "confidence_pct": "0.0%"
    }

    try:
        # === 1. Fetch Data (Intraday 1h) ===
        try:
            data = yf.download(ticker, period="60d", interval="1h", progress=False)
        except Exception as e:
            if debug_local: st.write(f"DEBUG: yfinance download failed for {ticker}: {e}")
            return out

        # Normalize columns: flatten MultiIndex & lowercase
        try:
            if isinstance(data.columns, pd.MultiIndex):
                # ambil level 0
                data.columns = [c[0] for c in data.columns]
            data.columns = [str(c).lower() for c in data.columns]
        except Exception:
            # biarkan apa adanya tapi lanjutkan
            pass

        # Jika kosong -> return
        if data is None or data.empty:
            if debug_local: st.write(f"DEBUG: Tidak ada data intraday untuk {ticker}")
            return out

        # Pastikan kolom volume ada dan filter volume > 0 (jika ingin)
        if 'volume' in data.columns:
            try:
                data = data[data['volume'] > 0].copy()
            except Exception:
                # jika filter gagal, biarkan data apa adanya
                pass

        # Minimal bar
        if len(data) < 50:
            if debug_local: st.write(f"DEBUG: Data intraday {ticker} tidak cukup (< 50 baris)")
            return out

        # Reset index & temukan kolom datetime secara robust
        try:
            data = data.reset_index()
            dt_cols = [c for c in data.columns if pd.api.types.is_datetime64_any_dtype(data[c])]
            if dt_cols:
                dt_col = dt_cols[0]
            else:
                # coba beberapa nama umum
                dt_candidates = ['datetime', 'date', 'time', 'index']
                dt_col = None
                for p in dt_candidates:
                    if p in data.columns:
                        try:
                            data[p] = pd.to_datetime(data[p], errors='coerce')
                            if pd.api.types.is_datetime64_any_dtype(data[p]):
                                dt_col = p
                                break
                        except Exception:
                            continue
                if dt_col is None:
                    # fallback ke kolom pertama
                    dt_col = data.columns[0]
                    try:
                        data[dt_col] = pd.to_datetime(data[dt_col], errors='coerce')
                    except Exception:
                        pass
            # rename to 'ds' for prophet compatibility later
            data = data.rename(columns={dt_col: 'ds'})
            # ensure timezone naive
            try:
                data['ds'] = pd.to_datetime(data['ds'], errors='coerce')
                # if tz-aware, remove tz
                if pd.api.types.is_datetime64tz_dtype(data['ds']) or data['ds'].dt.tz is not None:
                    data['ds'] = data['ds'].dt.tz_convert(None).dt.tz_localize(None)
            except Exception:
                # ignore tz errors
                pass
        except Exception as e:
            if debug_local: st.write(f"DEBUG: Error processing datetime for {ticker}: {e}")

        # Lowercase columns again to be safe
        data.columns = [str(c).lower() for c in data.columns]

        # === 2. Hitung Indikator TA ===
        try:
            # pandas_ta memerlukan kolom open/high/low/close/volume dengan nama tertentu (lowercase)
            # Pastikan kolom exist; jika tidak, abort TA
            required_cols = ['open', 'high', 'low', 'close']
            if not all(col in data.columns for col in required_cols):
                if debug_local: st.write(f"DEBUG: Kolom OHLC tidak lengkap untuk {ticker} -> {data.columns.tolist()}")
                return out

            # compute indicators (append=True menambahkan kolom ke dataframe)
            data.ta.bbands(length=20, std=2, append=True)
            data.ta.rsi(length=14, append=True)
            data.ta.macd(fast=12, slow=26, signal=9, append=True)

            # Standardize column names to lowercase again (pandas_ta sometimes capitalizes)
            data.columns = [str(c).lower() for c in data.columns]

            # Drop rows with NA produced by indicators
            data = data.dropna().reset_index(drop=True)
            if data.empty:
                if debug_local: st.write(f"DEBUG: Data {ticker} habis setelah kalkulasi TA & dropna.")
                return out
        except Exception as e:
            if debug_local: st.write(f"DEBUG: Gagal kalkulasi pandas_ta untuk {ticker}: {e}")
            return out

        # === 3. Ambil Nilai Terkini (safe) ===
        if len(data) < 2:
            if debug_local: st.write(f"DEBUG: Tidak cukup bar untuk {ticker} (len={len(data)})")
            return out

        try:
            last_row = data.iloc[-1]
            prev_row = data.iloc[-2]
        except Exception as e:
            if debug_local: st.write(f"DEBUG: Gagal ambil last/prev row untuk {ticker}: {e}")
            return out

        # get close price safe
        current_price = safe_get(last_row, 'close', None)
        try:
            current_price = float(current_price) if current_price is not None else None
        except Exception:
            current_price = None

        if current_price is None:
            if debug_local: st.write(f"DEBUG: Harga close tidak tersedia untuk {ticker}")
            return out

        out['current_price'] = current_price

        # indicators safe-get
        last_rsi = safe_get(last_row, 'rsi_14', None)
        last_macd_hist = safe_get(last_row, 'macdh_12_26_9', None)
        macd_val = safe_get(last_row, 'macd_12_26_9', None)
        macd_sig = safe_get(last_row, 'macds_12_26_9', None)

        try:
            macd_status = "Naik" if (last_macd_hist is not None and float(last_macd_hist) > 0 and float(macd_val) > float(macd_sig)) else "Turun"
        except Exception:
            macd_status = "Naik" if (last_macd_hist and float(last_macd_hist) > 0) else "Turun"

        try:
            macd_just_crossed_up = (last_macd_hist is not None and float(last_macd_hist) > 0 and float(safe_get(prev_row, 'macdh_12_26_9', 0)) <= 0)
        except Exception:
            macd_just_crossed_up = False

        bb_lower = safe_get(last_row, 'bbl_20_2.0', safe_get(last_row, 'bbl_20_2', None))
        bb_mid = safe_get(last_row, 'bbm_20_2.0', safe_get(last_row, 'bbm_20_2', None))
        bb_upper = safe_get(last_row, 'bbu_20_2.0', safe_get(last_row, 'bbu_20_2', None))

        recent_data = data.iloc[-72:].copy()
        recent_low = recent_data['low'].min() if 'low' in recent_data.columns else recent_data['close'].min()
        recent_high = recent_data['high'].max() if 'high' in recent_data.columns else recent_data['close'].max()

        # === 4. Prediksi ML (sebagai sinyal sekunder) ===
        ml_pred_direction = 0
        ml_accuracy = 0.0
        ml_pred_str = "ML Tidak Ada"
        try:
            if MLPredictor is not None:
                predictor = MLPredictor()
                # some predictor.predict might expect dataframe with specific column names - try/catch
                try:
                    ml_accuracy, ml_pred_str = predictor.predict(data)
                    # normalize types
                    ml_accuracy = float(ml_accuracy) if ml_accuracy is not None else 0.0
                    ml_pred_direction = _parse_ml_direction(ml_pred_str)
                except Exception as e:
                    if debug_local: st.write(f"DEBUG: MLPredictor.predict error for {ticker}: {e}")
                    ml_pred_direction = 0
                    ml_accuracy = 0.0
                    ml_pred_str = "ML Gagal"
            else:
                ml_pred_str = "ML Module Missing"
        except Exception as e:
            if debug_local: st.write(f"DEBUG: MLPredictor init error for {ticker}: {e}")
            ml_pred_direction = 0
            ml_accuracy = 0.0
            ml_pred_str = "ML Gagal"

        ml_considered = (ml_pred_direction != 0) and (ml_accuracy >= ml_conf_threshold_local)

        # === 5. Prediksi Prophet (sebagai sinyal primer) ===
        prophet_target_high = current_price * 1.05  # fallback default
        prophet_target_low = current_price * 0.95
        try:
            # prepare df for prophet: ds, y (y should be numeric)
            df_prophet = data[['ds', 'close']].rename(columns={'close': 'y'}).dropna()
            # prophet expects 'ds' and 'y' with ds as datetime
            df_prophet['ds'] = pd.to_datetime(df_prophet['ds'], errors='coerce')
            # if not enough rows for Prophet, skip
            if df_prophet['y'].count() >= 30:
                prophet_model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
                prophet_model.add_seasonality(name='daily', period=1, fourier_order=5)
                prophet_model.fit(df_prophet)

                future = prophet_model.make_future_dataframe(periods=24, freq='H')
                forecast = prophet_model.predict(future)
                # try to take last 16-24 rows for tomorrow window
                try:
                    tomorrow_forecast = forecast.tail(16)
                    prophet_target_high = float(tomorrow_forecast['yhat_upper'].max())
                    prophet_target_low = float(tomorrow_forecast['yhat_lower'].min())
                except Exception:
                    # fallback to simple multipliers
                    prophet_target_high = current_price * 1.05
                    prophet_target_low = current_price * 0.95
            else:
                if debug_local: st.write(f"DEBUG: Prophet skipped for {ticker} (not enough rows {len(df_prophet)})")
        except Exception as e:
            if debug_local: st.write(f"DEBUG: Gagal Prophet untuk {ticker}: {e}")
            # keep defaults

        # === 6. Logika Rekomendasi Wajib ===
        try:
            buy_rec = current_price
            take_profit = prophet_target_high
            stop_loss = recent_low
            signal_source = "N/A"
            confidence = 0.5

            is_strong_up_signal = (ml_considered and ml_pred_direction == 1) or (prophet_target_high > (current_price * 1.02)) or (macd_just_crossed_up)
            is_strong_down_signal = (ml_considered and ml_pred_direction == -1) or (prophet_target_low < (current_price * 0.98))

            if is_strong_up_signal and (last_rsi is None or float(last_rsi) < 75):
                signal_source = "Momentum Naik"
                if ml_considered and ml_pred_direction == 1:
                    signal_source = "ML + Momentum"
                    confidence = ml_accuracy
                else:
                    confidence = 0.65

                buy_rec = current_price  # buy at market
                # use bb_upper if available
                if bb_upper is not None:
                    try:
                        take_profit = _round_price(min(prophet_target_high, float(bb_upper) * 1.01))
                    except Exception:
                        take_profit = _round_price(prophet_target_high)
                else:
                    take_profit = _round_price(prophet_target_high)

                try:
                    stop_loss = _round_price(max(recent_low, float(bb_mid) if bb_mid is not None else recent_low))
                except Exception:
                    stop_loss = _round_price(recent_low)

            elif is_strong_down_signal or (last_rsi is not None and float(last_rsi) >= 75):
                # Speculative / contrarian lowball buy
                if is_strong_down_signal:
                    signal_source = "Spekulatif (Contra)"
                    confidence = 0.40
                else:
                    signal_source = "Spekulatif (OB)"
                    confidence = 0.45

                # Buy low: choose plausible buy_rec among prophet_low, bb_lower, or 90% current price
                candidates = []
                try:
                    if prophet_target_low: candidates.append(float(prophet_target_low))
                except Exception:
                    pass
                try:
                    if bb_lower: candidates.append(float(bb_lower))
                except Exception:
                    pass
                try:
                    candidates.append(current_price * 0.90)
                except Exception:
                    pass
                try:
                    buy_rec = _round_price(max(candidates)) if candidates else _round_price(current_price * 0.9)
                except Exception:
                    buy_rec = _round_price(current_price * 0.9)

                try:
                    take_profit = _round_price(float(bb_mid) if bb_mid is not None else (current_price * 0.98))
                except Exception:
                    take_profit = _round_price(current_price * 0.98)
                stop_loss = _round_price(buy_rec * 0.97)

            else:
                # Neutral / Range trading
                signal_source = "Range Trading (Netral)"
                confidence = 0.50
                try:
                    buy_rec = _round_price(max(recent_low, bb_lower) if bb_lower is not None else recent_low)
                except Exception:
                    buy_rec = _round_price(recent_low)
                try:
                    take_profit = _round_price(min(recent_high, bb_upper) if bb_upper is not None else recent_high)
                except Exception:
                    take_profit = _round_price(recent_high)
                stop_loss = _round_price(buy_rec * 0.97)
        except Exception as e:
            if debug_local: st.write(f"DEBUG: Error in recommendation logic for {ticker}: {e}")
            return out

        # === 7. Hitung R/R & Status ===
        try:
            rr_ratio = 0
            # Validate numeric
            try:
                buy_val = float(buy_rec)
                tp_val = float(take_profit)
                sl_val = float(stop_loss)
            except Exception:
                buy_val, tp_val, sl_val = None, None, None

            if buy_val is None or tp_val is None or sl_val is None or tp_val <= buy_val or buy_val <= sl_val or sl_val <= 0:
                rr_ratio = 0
            else:
                potential_profit = tp_val - buy_val
                potential_loss = buy_val - sl_val
                rr_ratio = (potential_profit / potential_loss) if potential_loss > 0 else 0

            # Map to rating/status
            rr_rating = "🔴 Weak"
            status = "Tidak Rekomendasi"
            if rr_ratio >= 3:
                rr_rating = "💎 Elite"
                status = "Rekomendasi Premium"
            elif rr_ratio >= 2:
                rr_rating = "🟢 Strong"
                status = "Rekomendasi Kuat"
            elif rr_ratio >= 1:
                rr_rating = "🟡 Moderate"
                status = "Rekomendasi Biasa"
            else:
                rr_rating = "🔴 Weak"
                status = "Tidak Rekomendasi"

            if "Spekulatif" in signal_source and status in ["Rekomendasi Premium", "Rekomendasi Kuat"]:
                status = "Rekomendasi Biasa (Spekulatif)"

            confidence_pct = f"{confidence * 100:.1f}%"

            # Fill out output
            out.update({
                "ticker": ticker,
                "current_price": round(current_price, 2) if current_price is not None else None,
                "buy_rec": round(buy_val, 2) if buy_val is not None else None,
                "take_profit": round(tp_val, 2) if tp_val is not None else None,
                "stop_loss": round(sl_val, 2) if sl_val is not None else None,
                "status": status,
                "signal_source": signal_source,
                "rr_rating": rr_rating,
                "confidence_pct": confidence_pct
            })
        except Exception as e:
            if debug_local: st.write(f"DEBUG: Error computing RR for {ticker}: {e}")
            return out

    except Exception as e:
        # last-resort catch for whole function
        if debug_local: st.write(f"DEBUG: Unexpected error for {ticker}: {e}")
        return out

    return out
# --- AKHIR FUNGSI ANALISIS BARU ---

# =======================================================
# 'GATE' ATAU GERBANG (Kode Login tidak berubah)
# =======================================================
def check_password():
    """Minta password di session state."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    st.title("🔒 Halaman Admin Terproteksi")
    st.write("Halaman ini hanya untuk pemilik aplikasi. Silakan masukkan password untuk melanjutkan.")

    password = st.text_input("Masukkan Password Admin", type="password")

    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state["password_correct"] = True
            st.rerun()  # Muat ulang halaman setelah berhasil login
        else:
            st.error("Password salah ❌")

    return st.session_state["password_correct"]

if not check_password():
    st.stop()  # Hentikan eksekusi sisa halaman jika password salah

# =======================================================
# KONTEN HALAMAN RAHASIA ANDA (Mulai dari sini)
# =======================================================

st.title("🧪 Ruang Pengembang (Strategi Overnight)")
st.success("Password Diterima. Selamat Datang, Kreator!")
st.info("Logika di halaman ini menggunakan data **Intraday (1 Jam)** untuk strategi 'Beli Sore, Jual Besok'.")
st.markdown("---")

# --- 1. Fitur Cache ---
st.header("Manajemen Cache")
st.warning("Gunakan ini jika Anda baru saja mengubah kode di folder `analysis` atau `machine_learning` untuk memaksa aplikasi mengambil data/model baru.")
if st.button("HAPUS SEMUA CACHE APLIKASI", type="primary"):
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Cache telah dibersihkan! Aplikasi akan memuat ulang data baru.")
        st.rerun()
    except Exception as e:
        st.error(f"Gagal membersihkan cache: {e}")

st.markdown("---")

# --- 2. Fitur Screener Massal ---
st.header("Analisis Massal (Screener Overnight)")

with st.expander("Pengaturan Analisis Massal", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        ml_conf_local_percent = st.slider(
            "Ambang Keyakinan ML Minimal",
            min_value=40,
            max_value=100,
            value=50,
            step=5,
            format="%d%%"
        )
    with col2:
        debug_local = st.checkbox("Cetak Error/Debug internal (jika terjadi kegagalan)", False)

tickers_input = st.text_area(
    "Masukkan Ticker (dipisah koma, spasi, atau baris baru)",
    "BBCA, BBNI, BMRI, TLKM, ASII, GOTO, MDKA, AMMN, BRIS, ANTM",
    height=150
)

if st.button("Mulai Analisis Massal", type="primary"):
    tickers_raw = tickers_input.replace(",", " ").replace("\n", " ")
    tickers_list = [t.strip().upper() for t in tickers_raw.split() if t.strip()]

    if not tickers_list:
        st.error("Mohon masukkan setidaknya satu ticker.")
    else:
        results = []
        progress_bar = st.progress(0, text="Memulai analisis...")

        # Konversi % ke float
        ml_conf_threshold_float = ml_conf_local_percent / 100.0

        for i, ticker in enumerate(tickers_list):
            normalized_ticker = _normalize_ticker(ticker)
            progress_bar.progress((i + 1) / len(tickers_list), text=f"Menganalisis {normalized_ticker}...")

            try:
                # Panggil FUNGSI BARU
                result = get_overnight_recommendation(
                    normalized_ticker,
                    ml_conf_threshold_local=ml_conf_threshold_float,
                    debug_local=debug_local
                )
                if result:
                    results.append(result)
            except Exception as e:
                st.error(f"Gagal total menganalisis {normalized_ticker}: {e}")

        progress_bar.empty()

        if results:
            st.success(f"Analisis massal selesai untuk {len(results)} saham.")
            df = pd.DataFrame(results)

            # Atur indeks agar mulai dari 1
            df.index = np.arange(1, len(df) + 1)

            # Tampilan tabel profesional (Poin 8 & 9)
            st.write(f"Menampilkan {len(df)} hasil:")
            try:
                st.data_editor(
                    df,
                    column_config={
                        "ticker": st.column_config.TextColumn("Nama Saham", width="auto"),
                        "current_price": st.column_config.NumberColumn("Harga", format="Rp %d"),
                        "buy_rec": st.column_config.NumberColumn("Rekomendasi Beli (RP)", format="Rp %d"),
                        "take_profit": st.column_config.NumberColumn("Take Profit (RP)", format="Rp %d"),
                        "stop_loss": st.column_config.NumberColumn("Stop Loss (RP)", format="Rp %d"),
                        "status": st.column_config.TextColumn("Status", width="auto"),
                        "signal_source": st.column_config.TextColumn("Sumber Sinyal", width="auto"),
                        "rr_rating": st.column_config.TextColumn("Risk Reward Rating", width="auto"),
                        "confidence_pct": st.column_config.TextColumn("Prediksi (%)", width="auto"),
                    },
                    column_order=(
                        "ticker",
                        "current_price",
                        "buy_rec",
                        "take_profit",
                        "stop_loss",
                        "status",
                        "signal_source",
                        "rr_rating",
                        "confidence_pct"
                    ),
                    use_container_width=True,
                    height=min(600, (len(df) + 1) * 35 + 3)
                )
            except Exception as e:
                st.error(f"Gagal menampilkan tabel hasil: {e}")
        else:
            st.warning("Tidak ada hasil untuk ditampilkan.")

st.markdown("---")
st.info(
    """
    **Catatan Developer:** Logika di halaman ini (`get_overnight_recommendation`)
    sepenuhnya **berbeda** dari halaman 4 (`Rekomendasi Premium`).

    Halaman ini khusus untuk menguji strategi **Intraday / Overnight** (beli sore, jual besok)
    menggunakan data per jam.
    """
)
