#pages/ 4_🎯_Rekomendasi_Premium.py

from utils.auth import check_password
import streamlit as st
import pandas as pd
import numpy as np
from prophet import Prophet
import time

# --- PENTING: Impor dari root folder ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ----------------------------------------

try:
    from analysis.analyzer import fetch_and_analyze_data
    from machine_learning.predictor import MLPredictor
    from constants import *
except ImportError:
    st.error("Gagal mengimpor modul. Pastikan Anda menjalankan Streamlit dari folder root 'pro-stock-analyzer'.")
    st.stop()

# ==========================================================
# PASSWORD ANDA DI SINI
# ==========================================================

if not check_password("🎯 Rekomendasi Premium"):
    st.stop()  # Hentikan eksekusi sisa skrip jika password salah

# --- Jika lolos, lanjutkan ke konten admin ---
st.success("Password Diterima. Selamat Datang, Kreator!")

# ==========================================================

# UI: ML confidence threshold sebagai persen (user friendly)
ml_conf_threshold_pct = st.sidebar.slider(
    "Ambang keyakinan ML (%). Hanya terima sinyal jika >= persen ini",
    min_value=50, max_value=95, value=65, step=1
)
# NOTE: ada juga slider akurasi ML (0..1) untuk pengaturan lain (tetap dipertahankan)
ml_accuracy_threshold = st.sidebar.slider("Ambang Akurasi ML minimal (0..1)", min_value=0.0, max_value=1.0, value=0.55, step=0.01)

# ==========================================================
# KONFIGURASI HALAMAN
# ==========================================================
st.set_page_config(
    page_title="Rekomendasi Premium",
    page_icon="🎯",
    layout="wide"
)
st.title("🎯 Rekomendasi Trader (Premium)")
st.markdown(
    """
    <style>
        .stButton>button {border: 2px solid #00FFFF; color: #00FFFF;}
        .stAlert {font-size: 1.1em;}
        h1, h2, h3 {font-family: 'Segoe UI', sans-serif;}
        [data-testid="stMetricDelta"] div { color: inherit !important; }
        [data-testid="stMetricDelta"] svg { fill: currentColor !important; }
    </style>
    """, unsafe_allow_html=True
)

# ==========================================================
# PENGATURAN (UI GLOBAL / PREFERENSI)
# ==========================================================
st.sidebar.header("Pengaturan Analisis")
mode = st.sidebar.selectbox("Mode Analisis", ["Konservatif", "Seimbang", "Agresif"], index=1,
                            help="Konservatif=butuh bukti kuat (ML+TA), Seimbang=ML+TA atau TA kuat, Agresif=terima TA-only juga")
allow_ta_only_default = True if mode == "Agresif" else False
allow_ta_only = st.sidebar.checkbox("Izinkan TA-only Buy Signals", value=allow_ta_only_default,
                                    help="Jika aktif, sinyal teknikal (MACD+RSI) dapat merekomendasikan BUY walau ML netral / tidak tersedia")
ml_accuracy_threshold = st.sidebar.slider("Ambang Akurasi ML minimal ({} mode)".format(mode), min_value=0.0, max_value=1.0, value=0.55 if mode=="Seimbang" else (0.6 if mode=="Konservatif" else 0.45), step=0.01)
show_debug = st.sidebar.checkbox("Debug Mode (tampilkan nilai indikator)", value=False)

# ==========================================================
# FUNGSI HELPER
# ==========================================================

def _normalize_ticker(ticker: str) -> str:
    """Memastikan ticker dalam format uppercase dan diakhiri .JK"""
    ticker = str(ticker).upper().strip()
    if ticker and not ticker.endswith(".JK"):
        ticker += ".JK"
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
    return int(base * round(price / base))


# ===== Helper mapping robust ML output =====
def _parse_ml_direction(ml_pred_str):
    """Return -1/0/1 robustly from ML output string or numeric."""
    if ml_pred_str is None:
        return 0
    try:
        s = str(ml_pred_str).upper().strip()
    except Exception:
        return 0

    # keywords indicative
    up_keywords = ["NAIK", "BUY", "UP", "RISE", "INCREASE", "POS", "+", "1", "BULL"]
    down_keywords = ["TURUN", "SELL", "DOWN", "FALL", "DECREASE", "NEG", "-", "-1", "BEAR"]

    if any(k in s for k in up_keywords):
        return 1
    if any(k in s for k in down_keywords):
        return -1

    # try parse numeric
    try:
        num = float(s)
        if num > 0.1:
            return 1
        if num < -0.1:
            return -1
    except Exception:
        pass
    return 0


# ==========================================================
# FUNGSI REKOMENDASI BELI (REVISI LOGIKA)
# ==========================================================

def get_buy_recommendation_analysis(ticker: str, allow_ta_only_local: bool = None, ml_conf_threshold_local: float = None, debug_local: bool = None):
    # fallback ke global jika param None (sama seperti sebelumnya)
    if allow_ta_only_local is None:
        allow_ta_only_local = allow_ta_only
    if ml_conf_threshold_local is None:
        ml_conf_threshold_local = ml_accuracy_threshold
    if debug_local is None:
        debug_local = show_debug

    analyzed_data = fetch_and_analyze_data(ticker, "1y", "1d")
    if analyzed_data is None or analyzed_data.empty:
        if debug_local:
            st.write({"ticker": ticker, "note": "no data returned from fetch_and_analyze_data"})
        st.error(f"Gagal mendapatkan data analisis untuk {ticker}.")
        return None
    if len(analyzed_data) < 3:
        st.warning(f"Data untuk {ticker} terlalu pendek untuk analisis (butuh minimal 3 bar).")
        return None

    # ---------- helper small funcs ----------
    def _safe_float(x, default=np.nan):
        try: return float(x)
        except Exception: return default

    def _parse_ml_conf(ml_str, accuracy):
        # coba ekstrak probabilitas dari string ml_pred_str jika format "UP:0.72" atau "PROB=0.72"
        if not isinstance(ml_str, str):
            return accuracy
        import re
        m = re.search(r"(\d?\.\d+)", ml_str)
        if m:
            try:
                val = float(m.group(1))
                # jika val tampak seperti akurasi/probabilitas (0..1 atau 0..100)
                if 0.0 <= val <= 1.0:
                    return max(val, accuracy*0.5)  # prefer explicit prob but keep floor
                if 1.0 < val <= 100.0:
                    return max(val/100.0, accuracy*0.5)
            except:
                pass
        return accuracy

    def _get_atr(df, period=14):
        # df must have High, Low, Close
        try:
            high = df['High']
            low = df['Low']
            close = df['Close']
            tr1 = high - low
            tr2 = (high - close.shift(1)).abs()
            tr3 = (low - close.shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period, min_periods=1).mean().iloc[-1]
            return float(atr) if not np.isnan(atr) else None
        except Exception:
            return None

    def _ensure_price(x):
        try: return float(x)
        except: return None

    # assume _round_price exists in your codebase; fallback naive:
    try:
        _ = _round_price(1.23)
        def _r(x): return _round_price(x) if x is not None else None
    except Exception:
        def _r(x):
            try:
                return round(float(x), 2)
            except:
                return x

    # ---------- ML block (sama, tapi parse confidence) ----------
    accuracy = 0.0
    ml_pred_str = "Data N/A"
    ml_pred_direction = 0
    ml_failed_due_to_data = False
    try:
        if len(analyzed_data) < 70:
            ml_failed_due_to_data = True
            accuracy = 0.0
            ml_pred_str = "Data N/A"
            ml_pred_direction = 0
        else:
            try:
                predictor = MLPredictor()
                accuracy, ml_pred_str = predictor.predict(analyzed_data)
                ml_pred_direction = _parse_ml_direction(ml_pred_str)
            except Exception as e_ml:
                if debug_local:
                    st.write(f"ML predictor error: {e_ml}")
                ml_failed_due_to_data = True
                accuracy = 0.0
                ml_pred_str = "ML Error"
                ml_pred_direction = 0
    except Exception as e:
        if debug_local:
            st.write(f"ML outer error: {e}")
        ml_failed_due_to_data = True
        accuracy = 0.0
        ml_pred_str = "ML Error"
        ml_pred_direction = 0

    # try to derive ML probability/confidence
    ml_prob = _parse_ml_conf(ml_pred_str, accuracy)

    # === Normalize threshold (UI pakai persen) dan siapkan tampilan persen ===
    try:
        thr = float(ml_conf_threshold_local)
        # Jika user mengirim 65 (persen) ubah ke 0.65
        if thr > 1.0:
            ml_prob_threshold = thr / 100.0
        else:
            ml_prob_threshold = thr
    except Exception:
        ml_prob_threshold = 0.65  # fallback aman

    try:
        ml_prob_pct_display = f"{ml_prob*100:.0f}%"
        ml_threshold_pct_display = f"{ml_prob_threshold*100:.0f}%"
    except Exception:
        ml_prob_pct_display = "N/A"
        ml_threshold_pct_display = "N/A"

    # ---------- ML decisions (pakai threshold yang di-convert) ----------
    ml_buy_confident = (ml_pred_direction == 1) and (ml_prob >= ml_prob_threshold)
    ml_sell_confident = (ml_pred_direction == -1) and (ml_prob >= ml_prob_threshold)
    ml_neutral = not (ml_buy_confident or ml_sell_confident)

    # ---------- Prophet (tetap sama, ringkas) ----------
    prophet_days = 14
    df_reset = analyzed_data.reset_index()
    ds_col = None
    for c in df_reset.columns[:3]:
        try:
            _ = pd.to_datetime(df_reset[c])
            ds_col = c
            break
        except Exception:
            continue
    if ds_col is None:
        try:
            ds_series = pd.to_datetime(analyzed_data.index)
            y_series = pd.to_numeric(analyzed_data['Close'], errors='coerce')
            df_prophet = pd.DataFrame({"ds": ds_series, "y": y_series})
        except Exception:
            df_prophet = pd.DataFrame({"ds": pd.Series([], dtype='datetime64[ns]'), "y": pd.Series([], dtype='float')})
    else:
        try:
            ds_series = pd.to_datetime(df_reset[ds_col])
            y_series = pd.to_numeric(df_reset['Close'], errors='coerce')
            df_prophet = pd.DataFrame({'ds': ds_series, 'y': y_series})
        except Exception:
            df_prophet = pd.DataFrame({'ds': pd.Series([], dtype='datetime64[ns]'), "y": pd.Series([], dtype='float')})

    try:
        if pd.api.types.is_datetime64_any_dtype(df_prophet['ds']):
            if df_prophet['ds'].dt.tz is not None:
                df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)
    except Exception:
        pass

    yearly_seasonality = len(df_prophet) >= 365
    prophet_upper_target = float(analyzed_data['Close'].iloc[-1]) * 1.05
    try:
        if len(df_prophet) >= 30 and df_prophet['y'].notna().sum() >= 30:
            prophet_model = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=yearly_seasonality)
            df_fit = df_prophet.dropna(subset=['y'])
            if len(df_fit) >= 30:
                prophet_model.fit(df_fit)
                future = prophet_model.make_future_dataframe(periods=prophet_days)
                forecast = prophet_model.predict(future)
                if len(forecast) >= 1:
                    prophet_upper_target = float(forecast['yhat_upper'].iloc[-1])
    except Exception as e_prophet:
        if debug_local:
            st.write(f"Prophet error: {e_prophet}")
        # fallback

    # ---------- TA ----------
    try:
        support_level_short = float(analyzed_data['Low'].iloc[-20:].min())
        resistance_level_short = float(analyzed_data['High'].iloc[-20:].max())
    except Exception:
        support_level_short = float(analyzed_data['Low'].min())
        resistance_level_short = float(analyzed_data['High'].max())
    try:
        support_level_med = float(analyzed_data['Low'].iloc[-60:].min())
        resistance_level_med = float(analyzed_data['High'].iloc[-60:].max())
    except Exception:
        support_level_med = support_level_short
        resistance_level_med = resistance_level_short

    current_price = float(analyzed_data['Close'].iloc[-1])
    last_row = analyzed_data.iloc[-1]
    prev_row = analyzed_data.iloc[-2] if len(analyzed_data) > 1 else analyzed_data.iloc[-1]

    last_rsi = _safe_float(last_row.get('RSI', np.nan))
    last_macd = _safe_float(last_row.get('MACD', np.nan))
    last_macd_sig = _safe_float(last_row.get('MACD_Signal', np.nan))

    rsi_status = "Overbought" if last_rsi > RSI_OVERBOUGHT else "Oversold" if last_rsi < RSI_OVERSOLD else "Netral"
    rsi_exiting_oversold = False
    try:
        prev_rsi = _safe_float(prev_row.get('RSI', np.nan))
        rsi_exiting_oversold = (last_rsi > RSI_OVERSOLD and prev_rsi <= RSI_OVERSOLD)
    except Exception:
        rsi_exiting_oversold = False

    macd_status = "Tren Naik" if (not np.isnan(last_macd) and not np.isnan(last_macd_sig) and last_macd > last_macd_sig) else "Tren Turun"
    macd_just_crossed_up = False
    try:
        prev_macd = _safe_float(prev_row.get('MACD', np.nan))
        prev_macd_sig = _safe_float(prev_row.get('MACD_Signal', np.nan))
        macd_just_crossed_up = (last_macd > last_macd_sig and prev_macd <= prev_macd_sig)
    except Exception:
        macd_just_crossed_up = False

    # TA signals (revisi)
    ta_strong_buy = (macd_just_crossed_up or (macd_status == "Tren Naik" and rsi_exiting_oversold))
    ta_medium_buy = (macd_status == "Tren Naik" and rsi_status == "Netral")
    ta_positive = ta_strong_buy or ta_medium_buy
    ta_warning_overbought = (rsi_status == "Overbought")
    ta_negative = (macd_status == "Tren Turun")

    # ---------- ATR for volatility-based SL/TP ----------
    atr = _get_atr(analyzed_data, period=14) or 0.0
    if atr == 0 or np.isnan(atr):
        atr = max( (resistance_level_short - support_level_short) / 20.0, current_price * 0.005 )  # fallback sensible small value

    # ---------- Determine buy limit (prefer buy on support/pullback) ----------
    # Strategy: try to buy near short support (within 1% above support). If current price already below that, use current_price.
    buy_limit_candidate = min(current_price, support_level_short * 1.01)
    # But if support is extremely close to current (gap tiny), prefer small pullback price = current_price * 0.995
    if abs(current_price - support_level_short) / current_price < 0.01:
        buy_limit_candidate = min(buy_limit_candidate, current_price * 0.995)

    # ---------- Init outputs ----------
    rekomendasi_final = "Tahan / Pantau"
    tingkat_risiko = "N/A"
    persentase_keyakinan = 0.0
    explanation = ""
    buy_area_price = None
    target_profit_price = None
    stop_loss_price = None
    potential_profit_per_share = None
    potential_risk_per_share = None
    rr_status = "N/A"
    is_buy_signal = False
    signal_source = "N/A"

    # ---------- Priority decision logic (revisi agar R/R diperhitungkan dulu) ----------
    # Overbought -> tunggu koreksi (sama seperti Anda)
    if ta_warning_overbought:
        rekomendasi_final = "TUNGGU KOREKSI (WAIT)"
        tingkat_risiko = "Menengah (Tunggu Koreksi)"
        signal_source = "TA (Overbought)"
        persentase_keyakinan = 0.40
        is_buy_signal = False
        buy_area_price = _r(support_level_short)
        stop_loss_price = _r(buy_area_price * 0.96) if buy_area_price is not None else None
        target_profit_price = _r(min(resistance_level_short, buy_area_price * 1.12)) if buy_area_price is not None else None
        rr_status = "Tunggu di Support"
        explanation = (f"🟡 PEMANTAUAN: RSI Overbought ({last_rsi:.1f}). Tunggu pullback ke support ~{_r(support_level_short)}.")

    elif ml_buy_confident and ta_positive:
        # Strong combined signal: buat trade plan tapi validasi R/R
        signal_source = "ML+TA (Strong)"
        # Use buy_limit near support (prefer entry lower than current)
        buy_area_price = _r(buy_limit_candidate)
        # Stop loss based on ATR (1.5 * ATR) but at most 6% of buy
        sl_distance = max(atr * 1.5, buy_area_price * 0.02)
        stop_loss_price = _r(max(buy_area_price - sl_distance, 0.0))
        # Target: prefer resistance or prophet, but ensure target at least buy + 2*sl_distance
        target_from_res = resistance_level_short * 0.99
        target_from_prophet = prophet_upper_target * 0.99
        target_profit_price_raw = max(target_from_res, target_from_prophet, buy_area_price + sl_distance * 2.0, buy_area_price * 1.03)
        target_profit_price = _r(target_profit_price_raw)

        # compute profit/risk
        if stop_loss_price and target_profit_price and (target_profit_price > buy_area_price) and (buy_area_price > stop_loss_price):
            potential_profit_per_share = target_profit_price - buy_area_price
            potential_risk_per_share = buy_area_price - stop_loss_price
            rr_ratio = potential_profit_per_share / potential_risk_per_share if potential_risk_per_share > 0 else 0
            if rr_ratio >= 2.0:
                rr_status = "Baik ✅"
            elif rr_ratio >= 1.5:
                rr_status = "Cukup Baik ☑️"
            else:
                rr_status = "Kurang Ideal ⚠️"
        else:
            rr_status = "Tidak Valid ❌"

        # validate R/R minimal 1.8-2.0
        if rr_status == "Baik ✅":
            rekomendasi_final = "REKOMENDASI UTAMA (BELI)"
            tingkat_risiko = "Rendah - Menengah"
            is_buy_signal = True
            persentase_keyakinan = min(1.0, 0.5*ml_prob + 0.4*(1.0 if ta_strong_buy else 0.7) + 0.1)  # kombinasi
        else:
            rekomendasi_final = "Tahan / Pantau (R/R Buruk)"
            tingkat_risiko = "Menengah (R/R Buruk)"
            is_buy_signal = False
            explanation = ("🟡 Sinyal kuat tetapi R/R tidak cukup bagus. "
                           "Pertimbangkan menunggu pullback lebih rendah atau gunakan ukuran posisi kecil.")
            persentase_keyakinan = 0.30

    elif ta_positive and (ml_neutral or allow_ta_only_local):
        # TA-only speculative: require stricter R/R because ML tidak mendukung
        signal_source = "TA-ONLY"
        buy_area_price = _r(buy_limit_candidate)
        sl_distance = max(atr * 1.2, buy_area_price * 0.025)
        stop_loss_price = _r(max(buy_area_price - sl_distance, 0.0))
        target_profit_price_raw = max(resistance_level_short * 0.99, buy_area_price + sl_distance * 1.8, buy_area_price * 1.04)
        target_profit_price = _r(target_profit_price_raw)
        if stop_loss_price and target_profit_price and (target_profit_price > buy_area_price) and (buy_area_price > stop_loss_price):
            potential_profit_per_share = target_profit_price - buy_area_price
            potential_risk_per_share = buy_area_price - stop_loss_price
            rr_ratio = potential_profit_per_share / potential_risk_per_share if potential_risk_per_share > 0 else 0
            if rr_ratio >= 2.0:
                rr_status = "Baik ✅"
                rekomendasi_final = "REKOMENDASI SPEKULATIF (BELI)"
                tingkat_risiko = "Menengah"
                is_buy_signal = True
                persentase_keyakinan = 0.45
            else:
                rr_status = "Kurang Ideal ⚠️"
                rekomendasi_final = "Tahan / Pantau (R/R Buruk)"
                is_buy_signal = False
                persentase_keyakinan = 0.30
        else:
            rekomendasi_final = "JANGAN BELI (HINDARI)"
            tingkat_risiko = "Beresiko / Sinyal Lemah"
            is_buy_signal = False
            persentase_keyakinan = 0.0
            explanation = "TA memberikan sinyal tetapi target/SL tidak valid."

    elif ml_buy_confident and not ta_negative:
        # ML lead: be more cautious and require ML prob high + R/R check
        signal_source = "ML-Lead (TA Netral)"
        buy_area_price = _r(min(current_price, resistance_level_short * 0.995))
        sl_distance = max(atr * 1.5, buy_area_price * 0.025)
        stop_loss_price = _r(max(buy_area_price - sl_distance, 0.0))
        target_profit_price_raw = max(prophet_upper_target * 0.95, buy_area_price + sl_distance * 2.0, resistance_level_short * 0.99)
        target_profit_price = _r(target_profit_price_raw)
        if stop_loss_price and target_profit_price and (target_profit_price > buy_area_price) and (buy_area_price > stop_loss_price):
            potential_profit_per_share = target_profit_price - buy_area_price
            potential_risk_per_share = buy_area_price - stop_loss_price
            rr_ratio = potential_profit_per_share / potential_risk_per_share if potential_risk_per_share > 0 else 0
            if rr_ratio >= 2.0 and ml_prob >= max(ml_prob_threshold, 0.75):
                rekomendasi_final = "REKOMENDASI SPEKULATIF (BELI)"
                tingkat_risiko = "Menengah (ML-Lead)"
                is_buy_signal = True
                persentase_keyakinan = ml_prob
                rr_status = "Cukup Baik ☑️" if rr_ratio >= 1.8 else "Kurang Ideal ⚠️"
            else:
                rekomendasi_final = "Tahan / Pantau (R/R atau ML kurang kuat)"
                tingkat_risiko = "Menengah"
                is_buy_signal = False
                persentase_keyakinan = ml_prob * 0.6
                rr_status = "Tidak Valid ❌"
        else:
            rekomendasi_final = "JANGAN BELI (HINDARI)"
            tingkat_risiko = "Beresiko / Sinyal Lemah"
            is_buy_signal = False
            persentase_keyakinan = 0.0
            explanation = "ML sinyal naik tetapi target/SL tidak valid."

    elif ml_sell_confident:
        rekomendasi_final = "JANGAN BELI (HINDARI)"
        tingkat_risiko = "Sangat Beresiko"
        signal_source = "ML (Prediksi Turun)"
        persentase_keyakinan = ml_prob
        is_buy_signal = False
        explanation = f"🔴 ML memprediksi turun: {ml_pred_str} (confidence {ml_prob:.2f}). Hindari beli."

    else:
        rekomendasi_final = "JANGAN BELI (HINDARI)"
        tingkat_risiko = "Beresiko / Sinyal Lemah"
        signal_source = "Netral / Sinyal Lemah"
        persentase_keyakinan = 0.0
        if ml_failed_due_to_data:
            explanation = "⚠️ ANALISIS TIDAK TERSEDIA: Data historis kurang untuk analisis beli."
        else:
            explanation = (f"🔴 SINYAL BELI TIDAK DITEMUKAN. MACD: {macd_status}. RSI: {rsi_status} ({last_rsi:.1f}).")

    # --- Penjelasan debug versi 'bahasa bayi' (sangat sederhana) ---
    if debug_local:
        def _fmt_rp(x):
            try: return f"Rp {int(x):,}"
            except Exception:
                try: return f"Rp {float(x):,.0f}"
                except Exception: return str(x)

        explanation += "\n\n--- INFO SINGKAT (Mudah dibaca) ---\n"
        # ML
        if ml_pred_direction == 1:
            ml_text = "NAIK 🔺"
        elif ml_pred_direction == -1:
            ml_text = "TURUN 🔻"
        else:
            ml_text = "TIDAK JELAS ➖"
        try:
            prob_pct = f"{ml_prob*100:.0f}%"
        except Exception:
            prob_pct = f"{accuracy*100:.0f}%"
        explanation += f"Robot (ML): {ml_text}. Percaya: {prob_pct} (Threshold: {ml_threshold_pct_display}).\n"
        explanation += "  → Artinya: robot bilang apakah harga cenderung naik atau turun.\n"

        # MACD (momentum)
        try:
            macd_trend = "Sedang dorong ke ATAS (bullish) 🔼" if (not np.isnan(last_macd) and not np.isnan(last_macd_sig) and last_macd > last_macd_sig) else "Sedang dorong ke BAWAH (bearish) 🔽"
            explanation += f"Momentum (MACD): {macd_trend}.\n"
        except Exception:
            explanation += "Momentum (MACD): data tidak lengkap.\n"

        # RSI (kondisi jenuh beli/jual)
        try:
            if np.isnan(last_rsi):
                explanation += "RSI: tidak tersedia.\n"
            else:
                if last_rsi > RSI_OVERBOUGHT:
                    explanation += f"RSI: Overbought ({last_rsi:.0f}) — Banyak yang beli, hati-hati koreksi. ⚠️\n"
                elif last_rsi < RSI_OVERSOLD:
                    explanation += f"RSI: Oversold ({last_rsi:.0f}) — Pernah turun kuat, berpotensi naik. ✅\n"
                else:
                    explanation += f"RSI: Netral ({last_rsi:.0f}) — Biasa saja.\n"
        except Exception:
            explanation += "RSI: error membaca nilai.\n"

        # Volatilitas & level teknis
        try:
            explanation += f"Go-yang harga (ATR14): {_r(atr)} — besar = sering lompat-lompat.\n"
        except Exception:
            explanation += "ATR14: tidak tersedia.\n"

        try:
            explanation += f"Support (20): {_fmt_rp(_r(support_level_short))} | Resistance (20): {_fmt_rp(_r(resistance_level_short))}.\n"
        except Exception:
            explanation += "Support/Resistance: tidak tersedia.\n"

        # Rencana trade (jika ada)
        if buy_area_price:
            explanation += f"Harga masuk (limit): {_fmt_rp(_r(buy_area_price))}\n"
            explanation += f"Target (TP): {_fmt_rp(_r(target_profit_price))} | Stop Loss (SL): {_fmt_rp(_r(stop_loss_price))}\n"
            explanation += f"Rasio Risiko/Untung: {rr_status}\n"
            explanation += "  → Artinya: perbandingan seberapa besar untung vs rugi.\n"
        else:
            explanation += "Tidak ada rencana beli sekarang (tidak aman/target tidak cukup bagus).\n"

        explanation += "\nCatatan singkat: Ini hanya panduan robot. Jangan pakai semua uangmu. Mulai kecil dulu. ❤️\n"

    return {
        "ticker": ticker,
        "current_price": current_price,
        "recommendation": rekomendasi_final,
        "risk_level": tingkat_risiko,
        "success_percentage": persentase_keyakinan,
        "buy_area_price": buy_area_price,
        "target_profit_price": target_profit_price,
        "stop_loss_price": stop_loss_price,
        "potential_profit_per_share": potential_profit_per_share,
        "potential_risk_per_share": potential_risk_per_share,
        "rr_status": rr_status,
        "confidence": persentase_keyakinan,
        "explanation": explanation
    }


# ==========================================================
# FUNGSI REKOMENDASI JUAL (tidak banyak berubah, gunakan ml_threshold)
# ==========================================================

def get_sell_recommendation_analysis(ticker: str, buy_price: float, lots: int, ml_conf_threshold_local: float = None):
    if ml_conf_threshold_local is None:
        ml_conf_threshold_local = ml_accuracy_threshold

    # Normalize threshold (support persen input dari UI)
    try:
        thr = float(ml_conf_threshold_local)
        if thr > 1.0:
            ml_prob_threshold = thr / 100.0
        else:
            ml_prob_threshold = thr
    except Exception:
        ml_prob_threshold = ml_accuracy_threshold

    analyzed_data = fetch_and_analyze_data(ticker, "1y", "1d")
    if analyzed_data is None or analyzed_data.empty:
        return None

    ml_failed_due_to_data = False
    accuracy = 0.0
    ml_pred_str = "Data N/A"
    ml_pred_direction = 0

    if len(analyzed_data) < 70:
        ml_failed_due_to_data = True
    else:
        try:
            predictor = MLPredictor()
            accuracy, ml_pred_str = predictor.predict(analyzed_data)
            ml_pred_direction = _parse_ml_direction(ml_pred_str)
        except Exception as e_ml:
            if show_debug:
                st.write(f"Gagal menjalankan ML predictor: {e_ml}")
            ml_failed_due_to_data = True
            accuracy = 0.0
            ml_pred_str = "ML Error"
            ml_pred_direction = 0

    prophet_days = 7
    df_reset = analyzed_data.reset_index()
    ds_col = None
    for c in df_reset.columns[:3]:
        try:
            _ = pd.to_datetime(df_reset[c])
            ds_col = c
            break
        except Exception:
            continue
    if ds_col is None:
        df_prophet = pd.DataFrame({'ds': pd.to_datetime(analyzed_data.index), 'y': analyzed_data['Close'].values})
    else:
        df_prophet = pd.DataFrame({'ds': pd.to_datetime(df_reset[ds_col]), 'y': pd.to_numeric(df_reset['Close'], errors='coerce')})
    try:
        if df_prophet['ds'].dt.tz is not None:
            df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)
    except Exception:
        pass

    yearly_seasonality = len(df_prophet) >= 365

    prophet_upper_target = analyzed_data['Close'].iloc[-1]  # default fallback
    try:
        if len(df_prophet) >= 30 and df_prophet['y'].notna().sum() >= 30:
            prophet_model = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=yearly_seasonality)
            df_fit = df_prophet.dropna(subset=['y'])
            if len(df_fit) >= 30:
                prophet_model = Prophet(
                    daily_seasonality=False,
                    weekly_seasonality=True,
                    yearly_seasonality=yearly_seasonality
                )
            prophet_model.fit(df_fit)
            future = prophet_model.make_future_dataframe(periods=prophet_days)
            forecast = prophet_model.predict(future)
            if len(forecast) >= 1:
                prophet_upper_target = float(forecast['yhat_upper'].iloc[-1])
    except Exception as e_prop:
        if show_debug:
            st.write(f"Gagal Prophet: {e_prop}")

    last_60_days = analyzed_data.iloc[-60:]
    resistance_level = last_60_days['High'].max()
    current_price = analyzed_data['Close'].iloc[-1]
    last_row = analyzed_data.iloc[-1]

    rsi_status = "Overbought" if last_row.get('RSI', np.nan) > RSI_OVERBOUGHT else "Oversold" if last_row.get('RSI', np.nan) < RSI_OVERSOLD else "Netral"
    macd_status = "Tren Naik" if last_row.get('MACD', np.nan) > last_row.get('MACD_Signal', np.nan) else "Tren Turun"

    recommendation_price = None
    explanation = ""
    potential_profit = 0.0
    potential_profit_pct = 0.0

    quantity = max(0, int(lots)) * 100
    current_value = current_price * quantity
    initial_cost = buy_price * quantity if buy_price is not None else 0.0

    if initial_cost > 0:
        current_pnl_rp = current_value - initial_cost
        current_pnl_pct = (current_pnl_rp / initial_cost) * 100
    else:
        current_pnl_rp = current_value - initial_cost
        current_pnl_pct = 0.0

    is_currently_profit = current_pnl_rp > 0

    # Branch berdasarkan ML direction (jika meyakinkan)
    # Gunakan ml_prob_threshold (dinormalisasi di atas)
    try:
        # parse prob from ml_pred_str if possible
        ml_prob = 0.0
        if isinstance(ml_pred_str, str) and ':' in ml_pred_str:
            try:
                ml_prob = float(ml_pred_str.split(':')[1])
            except Exception:
                ml_prob = accuracy
        else:
            ml_prob = accuracy
    except Exception:
        ml_prob = accuracy

    if ml_pred_direction == -1 and ml_prob >= ml_prob_threshold:
        recommendation_price_raw = current_price
        recommendation_price = _round_price(recommendation_price_raw)
        potential_profit = (recommendation_price - buy_price) * quantity if buy_price is not None else 0.0
        potential_profit_pct = ((recommendation_price / buy_price - 1) * 100) if (buy_price and buy_price > 0) else 0.0

        if is_currently_profit:
            explanation = (
                f"📉 **ML Prediksi Turun** (Acc: {accuracy*100:.1f}%).\n"
                f"   - **Status Anda:** Profit Rp {current_pnl_rp:,.0f} ({current_pnl_pct:.2f}%).\n"
                f"   - Indikator: RSI {rsi_status} ({last_row.get('RSI', np.nan):.1f}), MACD {macd_status}.\n"
                f"   - **Rekomendasi:** **Realisasikan profit** jual di **Rp {recommendation_price:,.0f}**.\n"
                f"   - **Hasil Estimasi:** Profit Rp {potential_profit:,.0f} ({potential_profit_pct:.2f}%)."
            )
        else:
            explanation = (
                f"📉 **ML Prediksi Turun** (Acc: {accuracy*100:.1f}%).\n"
                f"   - **Status Anda:** Loss Rp {current_pnl_rp:,.0f} ({current_pnl_pct:.2f}%).\n"
                f"   - Indikator: RSI {rsi_status} ({last_row.get('RSI', np.nan):.1f}), MACD {macd_status}.\n"
                f"   - **Rekomendasi:** **Cut loss** jual di **Rp {recommendation_price:,.0f}**.\n"
                f"   - **Hasil Estimasi:** Loss Rp {potential_profit:,.0f} ({potential_profit_pct:.2f}%)."
            )

    elif ml_pred_direction == 1 and ml_prob >= ml_prob_threshold:
        potential_target_short = min(resistance_level, prophet_upper_target)
        target_price = resistance_level if potential_target_short <= current_price else potential_target_short
        recommendation_price_raw = target_price * 0.99
        min_profit_price = buy_price * 1.01 if buy_price and buy_price > 0 else recommendation_price_raw
        final_recommendation_raw = max(recommendation_price_raw, min_profit_price)
        recommendation_price = _round_price(final_recommendation_raw)

        potential_profit = (recommendation_price - buy_price) * quantity if buy_price is not None else 0.0
        potential_profit_pct = ((recommendation_price / buy_price - 1) * 100) if (buy_price and buy_price > 0) else 0.0

        explanation = (
            f"📈 **ML Prediksi Naik** (Acc: {accuracy*100:.1f}%).\n"
            f"   - **Status Anda:** {'Profit' if is_currently_profit else 'Loss'} Rp {current_pnl_rp:,.0f} ({current_pnl_pct:.2f}%).\n"
            f"   - TA: Resist Rp {resistance_level:,.0f}. Prophet ~Rp {prophet_upper_target:,.0f}.\n"
            f"   - Indikator: RSI {rsi_status} ({last_row.get('RSI', np.nan):.1f}), MACD {macd_status}.\n"
        )
        if recommendation_price_raw < min_profit_price:
            explanation += (
                f"   - **Catatan:** Target teknikal (Rp {target_price:,.0f}) dekat harga beli.\n"
                f"   - **Rekomendasi:** Target jual minimal **Rp {recommendation_price:,.0f}** (estimasi 1-2 minggu).\n"
                f"   - **Hasil Estimasi:** Profit tipis/BE sekitar Rp {potential_profit:,.0f} ({potential_profit_pct:.2f}%)."
            )
        else:
            explanation += (
                f"   - **Rekomendasi:** Target jual **Rp {recommendation_price:,.0f}** (estimasi 1-2 minggu).\n"
                f"   - **Hasil Estimasi:** Profit Rp {potential_profit:,.0f} ({potential_profit_pct:.2f}%)."
            )

    else:
        recommendation_price = None
        explanation = (
            f"⚠️ **Prediksi Arah Tidak Tersedia.**\n"
            f"   - {'(Data kurang)' if ml_failed_due_to_data else '(Sinyal ML tidak jelas)'}\n"
            f"   - **Status Anda:** {'Profit' if is_currently_profit else 'Loss'} Rp {current_pnl_rp:,.0f} ({current_pnl_pct:.2f}%).\n"
            f"   - Indikator: RSI {rsi_status} ({last_row.get('RSI', np.nan):.1f}), MACD {macd_status}. Resist: Rp {resistance_level:,.0f}.\n"
            f"   - **Rekomendasi:** **Tahan / Pantau**."
        )

    if quantity == 0:
        potential_profit = 0.0
        potential_profit_pct = 0.0

    return {
        "ticker": ticker,
        "buy_price": buy_price,
        "lots": lots,
        "current_price": current_price,
        "ml_prediction": ml_pred_str,
        "ml_accuracy": accuracy,
        "recommendation_price": recommendation_price,
        "potential_profit": potential_profit,
        "potential_profit_pct": potential_profit_pct,
        "explanation": explanation
    }


# ==========================================================
# BATCH ANALYSIS + HELPERS
# ==========================================================

def analyze_batch(ticker_list, allow_ta_only_local=None, ml_conf_threshold_local=None, debug_local=None):
    results = []
    for t in ticker_list:
        tt = _normalize_ticker(t)
        try:
            r = get_buy_recommendation_analysis(tt, allow_ta_only_local=allow_ta_only_local, ml_conf_threshold_local=ml_conf_threshold_local, debug_local=debug_local)
            if r:
                results.append(r)
            else:
                results.append({"ticker": tt, "recommendation": "ERROR/NO DATA"})
        except Exception as e:
            results.append({"ticker": tt, "recommendation": f"ERROR: {e}"})
    return pd.DataFrame(results)


# ==========================================================
# UI UTAMA (Tabs) - dengan opsi batch dan toggle
# ==========================================================

tab_buy, tab_sell = st.tabs(["🎯 Rekomendasi Beli (Premium)", "💰 Rekomendasi Jual (Premium)"])

# --- Helper: Safe formatting ---
def safe_format(value, prefix="Rp "):
    return f"{prefix}{value:,.0f}" if isinstance(value, (int, float)) else "N/A"
# --- TAB REKOMENDASI BELI ---
with tab_buy:
    st.header("Analisis Potensi Beli Jangka Pendek")

    # --- Single ticker form ---
    with st.form("buy_recommendation_form"):
        st.write("Masukkan simbol saham yang ingin dianalisis potensi belinya:")
        buy_rec_symbol_input = st.text_input("Simbol Saham", placeholder="Contoh: BBCA")
        buy_rec_submitted = st.form_submit_button("🔍 Dapatkan Rekomendasi Beli", use_container_width=True, type="primary")

    if buy_rec_submitted:
        if not buy_rec_symbol_input:
            st.error("Mohon isi simbol saham.")
        else:
            try:
                buy_rec_ticker = _normalize_ticker(buy_rec_symbol_input)
                with st.spinner("Menganalisis data saham..."):
                    buy_result = get_buy_recommendation_analysis(
                        buy_rec_ticker,
                        allow_ta_only_local=allow_ta_only,
                        ml_conf_threshold_local=ml_conf_threshold_pct,  # <-- pakai persen UI
                        debug_local=show_debug,
                    )

                if not buy_result:
                    st.warning("Tidak ada hasil analisis untuk simbol ini.")
                else:
                    st.subheader(f"Rekomendasi Beli untuk {buy_result.get('ticker', buy_rec_ticker)}")
                    st.metric("Harga Saat Ini", safe_format(buy_result.get('current_price')))

                    st.subheader(f"Status: {buy_result.get('recommendation', 'Tidak tersedia')}")

                    if buy_result.get('buy_area_price') is not None:
                        st.info(f"**Keyakinan Arah:** {buy_result.get('confidence', 0)*100:.1f}%")

                        rec_col1, rec_col2, rec_col3 = st.columns(3)
                        rec_col1.metric("🎯 Area Beli", safe_format(buy_result.get('buy_area_price')))
                        rec_col2.metric("🏆 Target Profit", safe_format(buy_result.get('target_profit_price')))
                        rec_col3.metric("🛡️ Stop Loss", safe_format(buy_result.get('stop_loss_price')))

                        st.markdown("**Analisis Risk/Reward:**")
                        rr_col1, rr_col2, rr_col3 = st.columns(3)
                        rr_col1.metric("💰 Potensi Profit", safe_format(buy_result.get('potential_profit_per_share')))
                        rr_col2.metric("💣 Potensi Risiko", safe_format(buy_result.get('potential_risk_per_share')), delta_color="inverse")
                        rr_col3.metric("📊 Status R/R", buy_result.get('rr_status', 'N/A'))

                    st.markdown("**Analisis & Penjelasan:**")
                    st.markdown(buy_result.get('explanation', '').replace("\n", "\n\n"))

                    st.warning(
                        f"🚨 **Penting:** Ini BUKAN nasihat finansial. Prediksi berdasarkan data historis "
                        f"(Confidence: {buy_result.get('confidence',0)*100:.1f}%) dan tidak menjamin profit. "
                        "Selalu lakukan riset Anda sendiri (DYOR) dan gunakan manajemen risiko."
                    )

            except Exception as e:
                st.error(f"Gagal memproses analisis: {e}")

    # --- Batch Analysis ---
    st.markdown("---")
    st.subheader("Analisis Batch (multi-ticker)")
    tickers_text = st.text_area("Masukkan simbol (pisah koma / baris baru)", height=120, placeholder="Contoh: BBCA, TLKM, BBRI")
    run_batch = st.button("🔁 Jalankan Analisis Batch")

    if run_batch:
        if not tickers_text.strip():
            st.error("Mohon masukkan minimal 1 simbol untuk batch.")
        else:
            try:
                raw = [x.strip() for x in tickers_text.replace('\r', '\n').replace(',', '\n').split('\n') if x.strip()]
                with st.spinner(f"Menjalankan analisis untuk {len(raw)} ticker..."):
                    df_res = analyze_batch(
                        raw,
                        allow_ta_only_local=allow_ta_only,
                        ml_conf_threshold_local=ml_conf_threshold_pct,  # <-- pakai persen UI
                        debug_local=show_debug,
                    )

                if df_res is not None and not df_res.empty:
                    st.dataframe(df_res[['ticker','recommendation','current_price','buy_area_price','target_profit_price','stop_loss_price','confidence']])
                    csv_bytes = df_res.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download hasil", csv_bytes, "hasil_analisis_batch.csv", "text/csv")
                else:
                    st.warning("Tidak ada hasil analisis yang tersedia.")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat analisis batch: {e}")

# --- TAB REKOMENDASI JUAL ---
with tab_sell:
    st.header("Analisis Rekomendasi Jual")
    with st.form("sell_recommendation_form"):
        st.write("Masukkan detail posisi saham Anda saat ini:")
        rec_col1, rec_col2, rec_col3 = st.columns(3)
        with rec_col1:
            rec_symbol_input = st.text_input("Simbol Saham", placeholder="Contoh: BBCA")
        with rec_col2:
            rec_buy_price = st.number_input("Harga Beli Anda (per lembar)", min_value=1.0, step=1.0)
        with rec_col3:
            rec_lots = st.number_input("Jumlah Lot", min_value=1, step=1)
        rec_submitted = st.form_submit_button("🔍 Dapatkan Rekomendasi Jual", use_container_width=True, type="primary")

    if rec_submitted:
        if not rec_symbol_input or rec_buy_price <= 0 or rec_lots <= 0:
            st.error("Mohon isi semua field dengan benar.")
        else:
            rec_ticker = _normalize_ticker(rec_symbol_input)
            sell_result = get_sell_recommendation_analysis(rec_ticker, rec_buy_price, rec_lots, ml_conf_threshold_local=ml_conf_threshold_pct)  # <-- pakai persen UI
            if sell_result:
                st.subheader(f"Rekomendasi Jual untuk {sell_result['ticker']}")
                with st.container():
                    res_col1, res_col2 = st.columns(2)
                    with res_col1:
                        st.metric("Harga Beli Anda", f"Rp {sell_result['buy_price']:,.0f}")
                        st.metric("Harga Saat Ini", f"Rp {sell_result['current_price']:,.0f}")
                    with res_col2:
                        rec_price = sell_result['recommendation_price']
                        st.metric("🎯 Rekomendasi Harga Jual", f"Rp {rec_price:,.0f}" if rec_price else "Tahan / Pantau")
                        if rec_price:
                            profit_color = "normal" if sell_result['potential_profit'] > 0 else "inverse" if sell_result['potential_profit'] < 0 else "off"
                            profit_val = sell_result.get('potential_profit', 0)
                            profit_pct = sell_result.get('potential_profit_pct', 0)
                            st.metric("💰 Estimasi P/L", f"Rp {profit_val:,.0f}", f"{profit_pct:.2f}%", delta_color=profit_color)

                        else:
                            st.info("Tidak ada target harga jual spesifik saat ini.")

                    st.markdown("**Analisis & Penjelasan:**")
                    st.markdown(sell_result['explanation'].replace("\n", "\n\n"))

                    st.warning(f"🚨 **Penting:** Prediksi berdasarkan data historis (Akurasi Arah ML: {sell_result.get('ml_accuracy',0)*100:.1f}%). Keputusan investasi ada di tangan Anda.")
