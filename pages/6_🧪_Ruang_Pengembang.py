from utils.auth import check_password
import plotly.graph_objects as go
import os
try:
    import streamlit as st
except Exception:
    st = None
import pandas as pd
import numpy as np
import yfinance as yf
# --- pandas_ta optional (tahan ImportError agar app tidak crash) ---
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except Exception as e:
    ta = None
    PANDAS_TA_AVAILABLE = False
    # gunakan safe warn jika streamlit tidak tersedia
    if st:
        try:
            st.warning("pandas_ta tidak tersedia — indikator teknikal otomatis dinonaktifkan. Tambahkan 'pandas_ta' ke requirements.txt dan redeploy untuk mengaktifkan.")
        except Exception:
            pass
    else:
        print("WARNING: pandas_ta tidak tersedia — indikator teknikal otomatis dinonaktifkan.")
    # (opsional) log debug untuk developer
    if st and hasattr(st, "session_state") and st.session_state.get("debug_mode", False):
        try:
            st.write(f"DEBUG: pandas_ta import error: {e}")
        except Exception:
            print("DEBUG: pandas_ta import error:", e)

from prophet import Prophet
import time
import sys

# --- PENTING: Impor dari root folder ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ----------------------------------------

try:
    # Kita masih pakai MLPredictor, tapi sebagai sinyal sekunder
    from machine_learning.predictor import MLPredictor
    from constants import *
except Exception as e:
    # Jika streamlit tersedia, peringatan di UI, jika tidak, cetak
    if st:
        try:
            st.warning(f"Imports warning: {e}")
        except Exception:
            print("Imports warning:", e)
    else:
        print("Imports warning:", e)
    MLPredictor = None

# ==========================================================
# PASSWORD ANDA DI SINI
# ==========================================================

if not check_password("🧪 Ruang Pengembang"):
    st.stop()  # Hentikan eksekusi sisa skrip jika password salah

# --- Jika lolos, lanjutkan ke konten admin ---
st.success("Password Diterima. Selamat Datang, Kreator!")

# ==========================================================

# set page config jika streamlit tersedia
if st:
    try:
        st.set_page_config(
            page_title="Ruang Pengembang",
            page_icon="🧪",
            layout="wide"
        )
    except Exception:
        # beberapa versi streamlit memanggil set_page_config lebih awal; jika error, abaikan
        pass

# ==========================================================
# Helper kecil
# ==========================================================

def _safe_rerun():
    """Panggil rerun yang tersedia pada versi Streamlit.
    Jika tidak tersedia, jangan crash — UI akan refresh pada interaksi berikutnya."""
    if not st:
        return
    try:
        rerun_fn = getattr(st, "experimental_rerun", None) or getattr(st, "rerun", None)
        if callable(rerun_fn):
            rerun_fn()
    except Exception:
        return


def _st_warn(msg):
    if st:
        try:
            st.warning(msg)
        except Exception:
            print("WARNING:", msg)
    else:
        print("WARNING:", msg)


def _st_info(msg):
    if st:
        try:
            st.info(msg)
        except Exception:
            print("INFO:", msg)
    else:
        print("INFO:", msg)

# ==========================================================
# FUNGSI HELPER (Tetap Sama, sudah bagus)
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
# FUNGSI ANALISIS BARU (Dipecah untuk Keterbacaan)
# ==========================================================

def _fetch_and_prepare_data(ticker: str, debug_local: bool = False):
    """Tahap 1: Ambil data yfinance dan bersihkan."""
    try:
        data = yf.download(ticker, period="60d", interval="1h", progress=False)
    except Exception as e:
        if debug_local:
            if st:
                try:
                    st.write(f"DEBUG: yfinance download failed for {ticker}: {e}")
                except Exception:
                    print("DEBUG: yfinance download failed for", ticker, e)
            else:
                print("DEBUG: yfinance download failed for", ticker, e)
        return None

    try:
        # Normalize columns: flatten MultiIndex & lowercase
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0] for c in data.columns]
        data.columns = [str(c).lower() for c in data.columns]

        if data is None or data.empty:
            if debug_local:
                _st_warn(f"DEBUG: Tidak ada data intraday untuk {ticker}")
            return None

        if 'volume' in data.columns:
            data = data[data['volume'] > 0].copy()

        if len(data) < 50:
            if debug_local:
                _st_warn(f"DEBUG: Data intraday {ticker} tidak cukup (< 50 baris)")
            return None

        # Reset index & temukan kolom datetime secara robust
        data = data.reset_index()
        dt_cols = [c for c in data.columns if pd.api.types.is_datetime64_any_dtype(data[c])]
        if dt_cols:
            dt_col = dt_cols[0]
        else:
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
                dt_col = data.columns[0]
                data[dt_col] = pd.to_datetime(data[dt_col], errors='coerce')

        data = data.rename(columns={dt_col: 'ds'})

        # ensure timezone naive
        data['ds'] = pd.to_datetime(data['ds'], errors='coerce')
        if pd.api.types.is_datetime64tz_dtype(data['ds']) or (hasattr(data['ds'], 'dt') and data['ds'].dt.tz is not None):
            try:
                data['ds'] = data['ds'].dt.tz_convert(None).dt.tz_localize(None)
            except Exception:
                # fallback: remove tz info by converting to naive datetime
                data['ds'] = pd.to_datetime(data['ds'].astype(str), errors='coerce')

        data.columns = [str(c).lower() for c in data.columns]
        return data

    except Exception as e:
        if debug_local:
            _st_warn(f"DEBUG: Error processing datetime/prepare data for {ticker}: {e}")
        return None


def _calculate_ta_indicators(data: pd.DataFrame, debug_local: bool = False):
    """Tahap 2: Hitung indikator TA menggunakan pandas_ta."""
    if not PANDAS_TA_AVAILABLE:
        if debug_local:
            _st_info("DEBUG: pandas_ta skipped (not available).")
        return data # Kembalikan data asli jika pandas_ta tidak ada

    try:
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_cols):
            if debug_local:
                _st_warn(f"DEBUG: Kolom OHLC tidak lengkap -> {data.columns.tolist()}")
            return None

        # compute indicators
        data.ta.bbands(length=20, std=2, append=True)
        data.ta.rsi(length=14, append=True)
        data.ta.macd(fast=12, slow=26, signal=9, append=True)

        data.columns = [str(c).lower() for c in data.columns]
        data = data.dropna().reset_index(drop=True)
        
        if data.empty:
            if debug_local:
                _st_warn("DEBUG: Data habis setelah kalkulasi TA & dropna.")
            return None
        
        return data
    except Exception as e:
        if debug_local:
            _st_warn(f"DEBUG: Gagal kalkulasi pandas_ta: {e}")
        return None


def _get_ml_signal(data: pd.DataFrame, ml_conf_threshold: float, debug_local: bool = False):
    """Tahap 3: Dapatkan sinyal sekunder dari MLPredictor."""
    if MLPredictor is None:
        return 0, 0.0, "ML Module Missing"
        
    try:
        predictor = MLPredictor()
        ml_accuracy, ml_pred_str = predictor.predict(data)

        # Normalisasi ml_accuracy: jika dalam range 0..1, biarkan; jika >1 asumsi percent dan bagi 100
        try:
            ml_accuracy = float(ml_accuracy) if ml_accuracy is not None else 0.0
            if ml_accuracy > 1.0:
                # asumsi value seperti 65.0 -> convert to 0.65
                ml_accuracy = ml_accuracy / 100.0
        except Exception:
            ml_accuracy = 0.0

        ml_pred_direction = _parse_ml_direction(ml_pred_str)
        return ml_pred_direction, ml_accuracy, ml_pred_str
    except Exception as e:
        if debug_local:
            _st_warn(f"DEBUG: MLPredictor error: {e}")
        return 0, 0.0, "ML Gagal"


def _get_prophet_forecast(data: pd.DataFrame, current_price: float, debug_local: bool = False):
    """Tahap 4: Dapatkan sinyal primer (target) dari Prophet."""
    prophet_target_high = current_price * 1.05  # fallback
    prophet_target_low = current_price * 0.95   # fallback
    
    try:
        df_prophet = data[['ds', 'close']].rename(columns={'close': 'y'}).dropna()
        df_prophet['ds'] = pd.to_datetime(df_prophet['ds'], errors='coerce')
        
        if df_prophet['y'].count() >= 30:
            prophet_model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
            prophet_model.add_seasonality(name='daily', period=1, fourier_order=5)
            prophet_model.fit(df_prophet)

            future = prophet_model.make_future_dataframe(periods=24, freq='H')
            forecast = prophet_model.predict(future)
            
            tomorrow_forecast = forecast.tail(16)
            prophet_target_high = float(tomorrow_forecast['yhat_upper'].max())
            prophet_target_low = float(tomorrow_forecast['yhat_lower'].min())
        else:
            if debug_local:
                _st_info(f"DEBUG: Prophet skipped (not enough rows {len(df_prophet)})")
                
    except Exception as e:
        if debug_local:
            _st_warn(f"DEBUG: Gagal Prophet: {e}")
        # biarkan nilai fallback
        
    return prophet_target_high, prophet_target_low


def _generate_trade_logic(current_price: float, signals: dict):
    """Tahap 5: Logika rekomendasi wajib berdasarkan sinyal."""
    
    # Ekstrak sinyal dari dictionary
    last_rsi = signals.get('last_rsi')
    macd_just_crossed_up = signals.get('macd_just_crossed_up', False)
    ml_pred_direction = signals.get('ml_pred_direction', 0)
    ml_accuracy = signals.get('ml_accuracy', 0.0)
    ml_conf_threshold = signals.get('ml_conf_threshold', 0.5)
    prophet_target_high = signals.get('prophet_target_high', current_price * 1.05)
    prophet_target_low = signals.get('prophet_target_low', current_price * 0.95)
    bb_upper = signals.get('bb_upper')
    bb_mid = signals.get('bb_mid')
    bb_lower = signals.get('bb_lower')
    recent_low = signals.get('recent_low', current_price * 0.95)
    recent_high = signals.get('recent_high', current_price * 1.05)

    # Pastikan last_rsi numeric bila ada
    try:
        last_rsi_val = float(last_rsi) if last_rsi is not None else None
    except Exception:
        last_rsi_val = None

    ml_considered = (ml_pred_direction != 0) and (ml_accuracy >= ml_conf_threshold)

    is_strong_up_signal = (ml_considered and ml_pred_direction == 1) or (prophet_target_high > (current_price * 1.02)) or (macd_just_crossed_up)
    is_strong_down_signal = (ml_considered and ml_pred_direction == -1) or (prophet_target_low < (current_price * 0.98))

    buy_rec = current_price
    take_profit = prophet_target_high
    stop_loss = recent_low
    signal_source = "N/A"
    confidence = 0.5

    if is_strong_up_signal and (last_rsi_val is None or last_rsi_val < 75):
        signal_source = "Momentum Naik"
        if ml_considered and ml_pred_direction == 1:
            signal_source = "ML + Momentum"
            confidence = ml_accuracy
        else:
            confidence = 0.65

        buy_rec = current_price
        tp_candidate = prophet_target_high
        if bb_upper is not None:
            try:
                tp_candidate = min(prophet_target_high, float(bb_upper) * 1.01)
            except Exception:
                tp_candidate = prophet_target_high
        take_profit = _round_price(tp_candidate)
        
        sl_candidate = recent_low
        if bb_mid is not None:
            try:
                sl_candidate = max(recent_low, float(bb_mid))
            except Exception:
                sl_candidate = recent_low
        stop_loss = _round_price(sl_candidate)

    elif is_strong_down_signal or (last_rsi_val is not None and last_rsi_val >= 75):
        signal_source = "Spekulatif (Contra)" if is_strong_down_signal else "Spekulatif (OB)"
        confidence = 0.40 if is_strong_down_signal else 0.45

        candidates = [c for c in [prophet_target_low, bb_lower, current_price * 0.90] if c is not None]
        try:
            buy_rec = _round_price(max(candidates)) if candidates else _round_price(current_price * 0.9)
        except Exception:
            buy_rec = _round_price(current_price * 0.9)
        
        tp_candidate = (current_price * 0.98)
        if bb_mid is not None:
            try:
                tp_candidate = float(bb_mid)
            except Exception:
                tp_candidate = current_price * 0.98
        take_profit = _round_price(tp_candidate)
        stop_loss = _round_price(buy_rec * 0.97)

    else:
        signal_source = "Range Trading (Netral)"
        confidence = 0.50
        br_candidate = recent_low
        if bb_lower is not None:
            try:
                br_candidate = max(recent_low, bb_lower)
            except Exception:
                br_candidate = recent_low
        buy_rec = _round_price(br_candidate)
        
        tp_candidate = recent_high
        if bb_upper is not None:
            try:
                tp_candidate = min(recent_high, bb_upper)
            except Exception:
                tp_candidate = recent_high
        take_profit = _round_price(tp_candidate)
        stop_loss = _round_price(buy_rec * 0.97)
        
    return buy_rec, take_profit, stop_loss, signal_source, confidence


def _calculate_rr_rating(buy_rec, take_profit, stop_loss, signal_source):
    """Tahap 6: Hitung R/R dan tentukan status akhir."""
    try:
        buy_val = float(buy_rec)
        tp_val = float(take_profit)
        sl_val = float(stop_loss)
    except Exception:
        buy_val, tp_val, sl_val = None, None, None

    rr_ratio = 0
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

    if "Spekulatif" in signal_source and status in ["Rekomendasi Premium", "Rekomendasi Kuat"]:
        status = "Rekomendasi Biasa (Spekulatif)"

    return rr_rating, status, buy_val, tp_val, sl_val


# --- FUNGSI UTAMA (ORCHESTRATOR) ---

def get_overnight_recommendation(ticker: str, ml_conf_threshold_local: float = 0.5, debug_local: bool = False):
    """
    Menganalisis ticker menggunakan data intraday (1h) untuk strategi
    beli sore - jual besok.
    Ini adalah fungsi utama yang memanggil helper di atas.
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
        # === 1. Fetch & Prepare Data ===
        data = _fetch_and_prepare_data(ticker, debug_local)
        if data is None or data.empty:
            return out

        # === 2. Hitung Indikator TA ===
        data_with_ta = _calculate_ta_indicators(data.copy(), debug_local)
        if data_with_ta is None or data_with_ta.empty:
            if debug_local and st:
                try:
                    st.write(f"DEBUG: Gagal kalkulasi TA untuk {ticker}")
                except Exception:
                    print("DEBUG: Gagal kalkulasi TA untuk", ticker)
            return out # Gagal di TA

        # === 3. Ambil Nilai Terkini (safe) ===
        if len(data_with_ta) < 2:
            if debug_local:
                _st_warn(f"DEBUG: Tidak cukup bar untuk {ticker} (len={len(data_with_ta)})")
            return out

        last_row = data_with_ta.iloc[-1]
        prev_row = data_with_ta.iloc[-2]

        current_price = safe_get(last_row, 'close', None)
        if current_price is None:
            if debug_local:
                _st_warn(f"DEBUG: Harga close tidak tersedia untuk {ticker}")
            return out
        current_price = float(current_price)
        out['current_price'] = current_price
        
        # Ambil semua sinyal TA
        last_rsi = safe_get(last_row, 'rsi_14')
        last_macd_hist = safe_get(last_row, 'macdh_12_26_9')
        macd_val = safe_get(last_row, 'macd_12_26_9')
        macd_sig = safe_get(last_row, 'macds_12_26_9')
        
        try:
            macd_just_crossed_up = (float(last_macd_hist) > 0 and float(safe_get(prev_row, 'macdh_12_26_9', 0)) <= 0)
        except Exception:
            macd_just_crossed_up = False

        bb_lower = safe_get(last_row, 'bbl_20_2.0', safe_get(last_row, 'bbl_20_2'))
        bb_mid = safe_get(last_row, 'bbm_20_2.0', safe_get(last_row, 'bbm_20_2'))
        bb_upper = safe_get(last_row, 'bbu_20_2.0', safe_get(last_row, 'bbu_20_2'))

        recent_data = data_with_ta.iloc[-72:].copy()
        recent_low = recent_data['low'].min() if 'low' in recent_data.columns else recent_data['close'].min()
        recent_high = recent_data['high'].max() if 'high' in recent_data.columns else recent_data['close'].max()

        # === 4. Prediksi ML (sebagai sinyal sekunder) ===
        ml_pred_direction, ml_accuracy, ml_pred_str = _get_ml_signal(
            data_with_ta, 
            ml_conf_threshold_local, 
            debug_local
        )

        # === 5. Prediksi Prophet (sebagai sinyal primer) ===
        prophet_target_high, prophet_target_low = _get_prophet_forecast(
            data_with_ta, 
            current_price, 
            debug_local
        )
        
        # === 6. Logika Rekomendasi ===
        # Kumpulkan semua sinyal ke dalam satu dictionary
        signals = {
            'last_rsi': last_rsi,
            'macd_just_crossed_up': macd_just_crossed_up,
            'ml_pred_direction': ml_pred_direction,
            'ml_accuracy': ml_accuracy,
            'ml_conf_threshold': ml_conf_threshold_local,
            'prophet_target_high': prophet_target_high,
            'prophet_target_low': prophet_target_low,
            'bb_upper': bb_upper,
            'bb_mid': bb_mid,
            'bb_lower': bb_lower,
            'recent_low': recent_low,
            'recent_high': recent_high
        }
        
        buy_rec, take_profit, stop_loss, signal_source, confidence = _generate_trade_logic(current_price, signals)

        # === 7. Hitung R/R & Status ===
        rr_rating, status, buy_val, tp_val, sl_val = _calculate_rr_rating(
            buy_rec, 
            take_profit, 
            stop_loss, 
            signal_source
        )

        # pastikan confidence numeric
        try:
            conf_val = float(confidence)
            if conf_val > 1.0 and conf_val <= 100.0:
                conf_val = conf_val / 100.0
        except Exception:
            conf_val = 0.0

        confidence_pct = f"{conf_val * 100:.1f}%"

        # Fill out output
        out.update({
            "current_price": round(current_price, 2),
            "buy_rec": round(buy_val, 2) if buy_val is not None else None,
            "take_profit": round(tp_val, 2) if tp_val is not None else None,
            "stop_loss": round(sl_val, 2) if sl_val is not None else None,
            "status": status,
            "signal_source": signal_source,
            "rr_rating": rr_rating,
            "confidence_pct": confidence_pct
        })

    except Exception as e:
        # last-resort catch untuk seluruh fungsi
        if debug_local:
            _st_warn(f"DEBUG: Unexpected error for {ticker}: {e}")
        return out # return default 'out'
    
    return out

# --- AKHIR FUNGSI ANALISIS BARU ---

if st:
    st.title("🧪 Ruang Pengembang (Strategi Overnight)")
    st.success("Password Diterima. Selamat Datang, Kreator!")
    st.info("Logika di halaman ini menggunakan data **Intraday (1 Jam)** untuk strategi 'Beli Sore, Jual Besok'.")
    st.markdown("---")

# --- 1. Fitur Cache ---
if st:
    st.header("Manajemen Cache")
    _st_warn("Gunakan ini jika Anda baru saja mengubah kode di folder `analysis` atau `machine_learning` untuk memaksa aplikasi mengambil data/model baru.")
    if st.button("HAPUS SEMUA CACHE APLIKASI", type="primary"):
        try:
            if hasattr(st, 'cache_data'):
                try:
                    st.cache_data.clear()
                except Exception:
                    pass
            if hasattr(st, 'cache_resource'):
                try:
                    st.cache_resource.clear()
                except Exception:
                    pass
            st.success("Cache telah dibersihkan! Aplikasi akan memuat ulang data baru.")
            _safe_rerun()
        except Exception as e:
            st.error(f"Gagal membersihkan cache: {e}")

    st.markdown("---")

# --- 2. Fitur Screener Massal (dengan dukungan single-ticker UI) ---
if st:
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
else:
    # fallback values untuk environment tanpa streamlit (testing)
    ml_conf_local_percent = 50
    debug_local = False
    tickers_input = "BBCA"

# ---- Helper kecil untuk single-ticker UI ----
def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    import numpy as _np
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = ma_up / (ma_down.replace(0, 1e-8))
    rsi = 100 - (100 / (1 + rs))
    return rsi


def render_single_ticker_ui(ticker_raw: str, ml_conf_threshold: float, debug: bool):
    """Tampilkan UI lengkap & visual menarik untuk 1 ticker. Versi aman terhadap pandas Series."""
    if st:
        st.header(f"📊 Detail Saham — {ticker_raw}")
    else:
        print("DETAIL:", ticker_raw)

    try:
        normalized = _normalize_ticker(ticker_raw)
    except Exception:
        normalized = ticker_raw.upper().strip()

    # 1) Dapatkan rekomendasi/analisis overnight (jika fungsi tersedia)
    result = None
    try:
        result = get_overnight_recommendation(
            normalized,
            ml_conf_threshold_local=ml_conf_threshold,
            debug_local=debug
        )
    except Exception as e:
        if st:
            st.warning(f"Gagal mengambil rekomendasi ML untuk {normalized}: {e}")
        else:
            print("Gagal mengambil rekomendasi ML for", normalized, e)

    # 2) Ambil data historis menggunakan yfinance (6 bulan default)
    try:
        hist = yf.download(normalized, period="6mo", interval="1d", progress=False, threads=False)
    except Exception as e:
        if st:
            st.error(f"Gagal mengambil data historis {normalized}: {e}")
        else:
            print("Gagal mengambil data historis", normalized, e)
        return

    if hist is None or hist.empty:
        if st:
            st.warning("Data historis tidak tersedia untuk ticker ini.")
        else:
            print("Data historis tidak tersedia for", normalized)
        return

    # pastikan sorting index naik
    hist = hist.sort_index()

    # Hitung indikator sederhana
    hist["MA20"] = hist["Close"].rolling(window=20, min_periods=1).mean()
    hist["MA50"] = hist["Close"].rolling(window=50, min_periods=1).mean()
    hist["RSI14"] = _compute_rsi(hist["Close"], period=14)

    # Ambil nilai scalar terbaru & sebelumnya (aman terhadap Series)
    try:
        latest_close = float(hist["Close"].iloc[-1])
    except Exception:
        latest_close = float(hist["Close"].values[-1])

    if len(hist["Close"].values) >= 2:
        try:
            prev_close = float(hist["Close"].iloc[-2])
        except Exception:
            prev_close = float(hist["Close"].values[-2])
    else:
        prev_close = latest_close

    # juga ambil MA/RSI sebagai scalar untuk perbandingan
    try:
        latest_ma20 = float(hist["MA20"].iloc[-1])
        latest_ma50 = float(hist["MA50"].iloc[-1])
        latest_rsi14 = float(hist["RSI14"].iloc[-1])
    except Exception:
        latest_ma20 = float(hist["MA20"].values[-1])
        latest_ma50 = float(hist["MA50"].values[-1])
        latest_rsi14 = float(hist["RSI14"].values[-1])

    # Hitung perubahan persentase dengan guard pembagi nol
    change_pct = (latest_close - prev_close) / prev_close * 100 if prev_close != 0 else 0.0

    # 3) Tata letak KPI & ringkasan cepat
    if st:
        k1, k2, k3 = st.columns(3)
        k1.metric("Harga Terakhir", f"Rp {int(latest_close):,}", delta=f"{change_pct:.2f}%")
        k2.metric("MA20", f"Rp {int(latest_ma20):,}")
        k3.metric("MA50", f"Rp {int(latest_ma50):,}")
    else:
        print(f"Harga Terakhir: Rp {int(latest_close):,} ({change_pct:.2f}%)")

    # Rekomendasi ML ringkas dari result (jika ada)
    if result and isinstance(result, dict):
        if st:
            rec_col1, rec_col2, rec_col3 = st.columns(3)
            rec_col1.metric("Rekomendasi Beli", f"Rp {int(result.get('buy_rec', 0)):,}" if result.get("buy_rec") else "—")
            rec_col2.metric("Take Profit", f"Rp {int(result.get('take_profit', 0)):,}" if result.get("take_profit") else "—")
            rec_col3.metric("Stop Loss", f"Rp {int(result.get('stop_loss', 0)):,}" if result.get("stop_loss") else "—")
            st.markdown(f"**Confidence ML:** {result.get('confidence_pct', '—')}")
            st.markdown(f"**Sumber Sinyal:** {result.get('signal_source', '—')}")
        else:
            print("ML Result:", result)
    else:
        if st:
            st.info("Tidak ada hasil rekomendasi ML atau rekomendasi tidak tersedia.")
        else:
            print("Tidak ada hasil rekomendasi ML atau rekomendasi tidak tersedia.")

    # 4) Grafik Candlestick + MA (gunakan go yang di-import di header)
    try:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            name="Candlestick"
        ))
        fig.add_trace(go.Scatter(x=hist.index, y=hist["MA20"], name="MA20", mode="lines"))
        fig.add_trace(go.Scatter(x=hist.index, y=hist["MA50"], name="MA50", mode="lines"))
        fig.update_layout(
            title=f"{normalized} — Candlestick & Moving Averages (6 bulan)",
            xaxis_title="Tanggal",
            yaxis_title="Harga",
            xaxis_rangeslider_visible=False,
            height=480
        )
        if st:
            st.plotly_chart(fig, use_container_width=True)
        else:
            print("Candlestick chart created for", normalized)
    except Exception as e:
        _st_warn(f"Gagal menampilkan grafik harga: {e}")

    # 5) Volume dan RSI di bawah
    try:
        if st:
            col_v, col_r = st.columns([2, 1])
            with col_v:
                fig_vol = go.Figure()
                fig_vol.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volume"))
                fig_vol.update_layout(title="Volume Per Hari", xaxis_title="Tanggal", yaxis_title="Volume", height=240)
                st.plotly_chart(fig_vol, use_container_width=True)
            with col_r:
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=hist.index, y=hist["RSI14"], name="RSI14", mode="lines"))
                fig_rsi.update_layout(title="RSI (14)", xaxis_title="Tanggal", yaxis_title="RSI", height=240)
                fig_rsi.add_hline(y=30, line_dash="dash", annotation_text="Oversold (30)", annotation_position="bottom left")
                fig_rsi.add_hline(y=70, line_dash="dash", annotation_text="Overbought (70)", annotation_position="top left")
                st.plotly_chart(fig_rsi, use_container_width=True)
        else:
            print("Volume/RSI plots created for", normalized)
    except Exception as e:
        _st_warn(f"Gagal menampilkan volume/RSI: {e}")

    # 6) Penjelasan & insight otomatis (berbasis indikator yang dihitung)
    if st:
        st.subheader("Insight & Penjelasan")
    else:
        print("Insight & Penjelasan:")
    insights = []
    # Trend berdasar MA (gunakan scalar)
    if latest_ma20 > latest_ma50:
        insights.append("- Tren harga jangka menengah **Bullish** (MA20 di atas MA50).")
    elif latest_ma20 < latest_ma50:
        insights.append("- Tren harga jangka menengah **Bearish** (MA20 di bawah MA50).")
    else:
        insights.append("- Tren harga netral (MA20 ≈ MA50).")

    # RSI interpretation (scalar)
    if latest_rsi14 < 30:
        insights.append("- RSI menunjukkan kondisi **oversold** (mungkin kesempatan beli, periksa fundamental & likuiditas).")
    elif latest_rsi14 > 70:
        insights.append("- RSI menunjukkan kondisi **overbought** (awas koreksi).")
    else:
        insights.append("- RSI berada di zona netral.")

    # Price momentum (gunakan change_pct scalar)
    if change_pct > 2:
        insights.append(f"- Harga naik tajam hari terakhir ({change_pct:.2f}%).")
    elif change_pct < -2:
        insights.append(f"- Harga turun tajam hari terakhir ({change_pct:.2f}%).")
    else:
        insights.append(f"- Pergerakan harga harian relatif tenang ({change_pct:.2f}%).")

    # Sertakan hasil rekomendasi ML jika ada
    if result and isinstance(result, dict):
        status = result.get("status", "")
        confidence = result.get("confidence_pct", "")
        insights.append(f"- Rekomendasi ML: **{status}** (Confidence: {confidence}).")
        if result.get("rr_rating"):
            insights.append(f"- Risk-Reward: {result.get('rr_rating')}")

    if st:
        st.markdown("\n".join(insights))
    else:
        print("\n".join(insights))

    # Tombol kecil untuk menampilkan raw dataframe hist jika developer butuh
    if st:
        with st.expander("Tampilkan data historis (raw)"):
            st.dataframe(hist.tail(200))
    else:
        pass

    return

# ---- Main: ketika tombol diklik ----
if st:
    if st.button("Mulai Analisis Massal", type="primary"):
        tickers_raw = tickers_input.replace(",", " ").replace("\n", " ")
        tickers_list = [t.strip().upper() for t in tickers_raw.split() if t.strip()]

        if not tickers_list:
            st.error("Mohon masukkan setidaknya satu ticker.")
        else:
            # Jika hanya 1 ticker diminta, tampilkan UI single-ticker dan *jangan* lanjut ke massal tabel
            if len(tickers_list) == 1:
                # Ambang ML dalam bentuk float
                ml_conf_threshold_float = ml_conf_local_percent / 100.0
                # Tampilkan UI lengkap untuk 1 saham
                render_single_ticker_ui(tickers_list[0], ml_conf_threshold_float, debug_local)
            else:
                # --- SALINAN LOGIKA MASSAL ANDA (TIDAK DIUBAH) ---
                results = []
                progress_bar = st.progress(0, text="Memulai analisis...")

                # Konversi % ke float
                ml_conf_threshold_float = ml_conf_local_percent / 100.0

                for i, ticker in enumerate(tickers_list):
                    normalized_ticker = _normalize_ticker(ticker)
                    progress_bar.progress((i + 1) / len(tickers_list), text=f"Menganalisis {normalized_ticker}...")

                    try:
                        # Panggil FUNGSI BARU (yang sudah di-refactor)
                        result = get_overnight_recommendation(
                            normalized_ticker,
                            ml_conf_threshold_local=ml_conf_threshold_float,
                            debug_local=debug_local
                        )
                        if result:
                            results.append(result)
                    except Exception as e:
                        # Ini seharusnya tidak terjadi karena fungsi utamanya sudah try/except
                        # tapi sebagai keamanan ekstra
                        st.error(f"Gagal total menganalisis {normalized_ticker}: {e}")
                        results.append({
                            "ticker": normalized_ticker,
                            "status": f"Fatal Error: {e}",
                            # ... isi sisa field dgn None/N/A
                        })


                progress_bar.empty()

                if results:
                    st.success(f"Analisis massal selesai untuk {len(results)} saham.")
                    df = pd.DataFrame(results)

                    df.index = np.arange(1, len(df) + 1)

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
                        st.dataframe(df) # Fallback ke dataframe biasa
                else:
                    st.warning("Tidak ada hasil untuk ditampilkan.")

# akhir
st.markdown("---")
if st:
    st.info(
        """
        **Catatan Developer:** Logika di halaman ini (`get_overnight_recommendation`)
        sepenuhnya **berbeda** dari halaman 4 (`Rekomendasi Premium`).

        Halaman ini khusus untuk menguji strategi **Intraday / Overnight** (beli sore, jual besok)
        menggunakan data per jam.
        """
    )