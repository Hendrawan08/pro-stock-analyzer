import traceback
import pandas as pd
import numpy as np
import streamlit as st

# Alias 'ta' (bukosabino) sebagai ta_lib agar tidak bentrok
try:
    import ta as ta_lib
except Exception:
    ta_lib = None

# pandas_ta (akses melalui accessor df.ta)
try:
    import pandas_ta as pta
except Exception:
    pta = None

# Prefer talib (C-library) untuk candlestick
try:
    import talib
except Exception:
    talib = None

# Import internal project modules
from data.data_manager import fetch_data
from indicators.moving_average import MovingAverage
from indicators.rsi import RSI
from indicators.macd import MACD
from indicators.bollinger_bands import BollingerBands
from indicators.stochastic import Stochastic
from patterns.reversal_patterns import ReversalPatterns
from constants import * # pastikan konstanta ada (RSI_OVERBOUGHT, RSI_OVERSOLD, dll.)

# ----------------- Helper: simple candlestick detectors (vectorized) -----------------
# ... (Semua fungsi helper Anda: detect_doji, detect_hammer, dll. tetap di sini) ...
def detect_doji(open_, high, low, close, tol=0.1):
    body = np.abs(close - open_)
    rng = high - low
    cond = (rng > 0) & (body <= tol * rng)
    return np.where(cond, 100, 0)  # 100 = Doji found

def detect_hammer(open_, high, low, close):
    body = np.abs(close - open_)
    upper = high - np.maximum(open_, close)
    lower = np.minimum(open_, close) - low
    cond = (lower >= 2 * body) & (upper <= 0.25 * body) & (body > 0)
    return np.where(cond, 100, 0)

def detect_shooting_star(open_, high, low, close):
    body = np.abs(close - open_)
    upper = high - np.maximum(open_, close)
    lower = np.minimum(open_, close) - low
    cond = (upper >= 2 * body) & (lower <= 0.25 * body) & (body > 0)
    return np.where(cond, -100, 0)  # -100 for bearish-type (shooting star)

def detect_engulfing(open_, high, low, close):
    prev_open = np.roll(open_, 1)
    prev_close = np.roll(close, 1)
    prev_body = np.abs(prev_close - prev_open)
    cur_body = np.abs(close - open_)
    bullish = (prev_close < prev_open) & (close > open_) & \
              (cur_body > prev_body) & (open_ < prev_close) & (close > prev_open)
    bearish = (prev_close > prev_open) & (close < open_) & \
             (cur_body > prev_body) & (open_ > prev_close) & (close < prev_open)
    res = np.zeros_like(close, dtype=int)
    res = np.where(bullish, 100, res)
    res = np.where(bearish, -100, res)
    res[0] = 0  # pertama tidak punya previous
    return res

def detect_morning_evening_star(open_, high, low, close):
    res_morning = np.zeros_like(close, dtype=int)
    res_evening = np.zeros_like(close, dtype=int)
    o = open_
    c = close
    o0 = np.roll(o, 2)  # bar0 (t-2)
    c0 = np.roll(c, 2)
    o1 = np.roll(o, 1)  # bar1 (t-1)
    c1 = np.roll(c, 1)
    o2 = o                # bar2 (t)
    c2 = c
    body0 = np.abs(c0 - o0)
    body1 = np.abs(c1 - o1)
    body2 = np.abs(c2 - o2)
    rng0 = np.maximum(o0, c0) - np.minimum(o0, c0)
    rng1 = np.maximum(o1, c1) - np.minimum(o1, c1)
    rng0 = np.where(rng0 == 0, 1e-9, rng0)
    rng1 = np.where(rng1 == 0, 1e-9, rng1)
    cond_morning = (c0 < o0) & (body1 <= 0.3 * rng1) & (c2 > o2) & (c2 > (o0 + c0) / 2)
    cond_evening = (c0 > o0) & (body1 <= 0.3 * rng1) & (c2 < o2) & (c2 < (o0 + c0) / 2)
    res_morning = np.where(cond_morning, 100, 0)
    res_evening = np.where(cond_evening, -100, 0)
    res_morning[:2] = 0
    res_evening[:2] = 0
    return res_morning, res_evening
# -----------------------------------------------

# ----------------- Fungsi utama -----------------
def fetch_and_analyze_data(ticker, period, interval):
    """
    Ambil data via fetch_data() lalu jalankan rangkaian indikator + pola candlestick.
    Versi: V10.2 (Base V10.1 + Momentum Change_10D)
    """
    data = fetch_data(ticker, period, interval)
    if data is None:
        st.warning(f"fetch_data mengembalikan None untuk {ticker}")
        return None

    try:
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required_cols):
            st.error(f"Data awal untuk {ticker} tidak lengkap. Kolom yang diperlukan: {required_cols}")
            return None

        data_analyzed = data.copy()

        # Pastikan numeric
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            data_analyzed[col] = pd.to_numeric(data_analyzed[col], errors='coerce')

        # Indikator dasar (external classes). Tangani jika ada error.
        try:
            data_analyzed = MovingAverage().calculate(data_analyzed)
        except Exception as e:
            st.warning(f"Gagal menghitung MovingAverage: {e}")

        try:
            data_analyzed = RSI().calculate(data_analyzed)
        except Exception as e:
            st.warning(f"Gagal menghitung RSI: {e}")

        try:
            data_analyzed = MACD().calculate(data_analyzed)
        except Exception as e:
            st.warning(f"Gagal menghitung MACD: {e}")

        try:
            data_analyzed = BollingerBands().calculate(data_analyzed)
        except Exception as e:
            st.warning(f"Gagal menghitung BollingerBands: {e}")

        try:
            data_analyzed = Stochastic().calculate(data_analyzed)
        except Exception as e:
            st.warning(f"Gagal menghitung Stochastic: {e}")

        # --- TAMBAHAN V10.2: Hitung Momentum Harga (10 Hari) ---
        try:
            momentum_window = min(10, max(2, len(data_analyzed))) # Window 10 hari, min 2
            if momentum_window > 1:
                # Hitung % perubahan dari 10 bar sebelumnya
                data_analyzed['Change_10D'] = data_analyzed['Close'].pct_change(periods=momentum_window) * 100
                data_analyzed['Change_10D'] = data_analyzed['Change_10D'].fillna(0) # Isi NaN di awal
            else:
                data_analyzed['Change_10D'] = 0.0
        except Exception as e_mom:
            st.warning(f"Gagal menghitung Momentum Harga (Change_10D): {e_mom}")
            data_analyzed['Change_10D'] = 0.0
        # -----------------------------------------------------------

        # Volume MA20 (Kode ini sudah ada di file Anda)
        try:
            vol_ma_window = min(20, max(2, len(data_analyzed)))
            data_analyzed['Volume_MA20'] = data_analyzed['Volume'].rolling(window=vol_ma_window).mean().fillna(0)
        except Exception as e_vol_ma:
            st.warning(f"Gagal menghitung Volume MA20: {e_vol_ma}")
            data_analyzed['Volume_MA20'] = 0

        # Reversal patterns internal
        try:
            data_analyzed = ReversalPatterns().detect_all(data_analyzed, interval)
        except Exception as e:
            st.warning(f"Gagal menjalankan ReversalPatterns.detect_all: {e}")

        # VWAP via ta_lib (jika ada)
        try:
            vwap_window = min(20, max(2, len(data_analyzed)))
            if ta_lib is not None and hasattr(ta_lib, 'volume') and vwap_window > 1:
                try:
                    vwap_obj = ta_lib.volume.VolumeWeightedAveragePrice(
                        high=data_analyzed['High'],
                        low=data_analyzed['Low'],
                        close=data_analyzed['Close'],
                        volume=data_analyzed['Volume'],
                        window=vwap_window,
                        fillna=True
                    )
                    if hasattr(vwap_obj, 'vwap'):
                        data_analyzed['VWAP_20'] = vwap_obj.vwap
                    else:
                        data_analyzed['VWAP_20'] = pd.NA
                except Exception as e_local:
                    st.warning(f"Gagal menghitung VWAP via ta_lib: {e_local}")
                    data_analyzed['VWAP_20'] = pd.NA
            else:
                data_analyzed['VWAP_20'] = data_analyzed['Close']
        except Exception as e_vwap:
            st.warning(f"Gagal menghitung VWAP untuk {ticker}: {e_vwap}")
            data_analyzed['VWAP_20'] = pd.NA

        # Sentiment score (jika kolom tersedia)
        try:
            req_score_cols = ['MA_M', 'MA_L', 'MACD', 'MACD_Signal', 'RSI']
            if all(col in data_analyzed.columns for col in req_score_cols):
                score_ma = np.where(data_analyzed['MA_M'] > data_analyzed['MA_L'], 35, 0)
                score_macd = np.where(data_analyzed['MACD'] > data_analyzed['MACD_Signal'], 35, 0)

                rsi_conditions = [
                    (data_analyzed['RSI'] <= RSI_OVERSOLD),
                    (data_analyzed['RSI'] < 50),
                    (data_analyzed['RSI'] < RSI_OVERBOUGHT),
                    (data_analyzed['RSI'] >= RSI_OVERBOUGHT)
                ]
                rsi_choices = [30, 20, 10, 0]
                score_rsi = np.select(rsi_conditions, rsi_choices, default=0)
                data_analyzed['Sentiment_Score'] = score_ma + score_macd + score_rsi
            else:
                st.warning(f"Gagal menghitung Skor Sentimen untuk {ticker}: Indikator dasar tidak lengkap.")
                data_analyzed['Sentiment_Score'] = 50
        except Exception as e_sc:
            st.warning(f"Error menghitung Sentiment_Score: {e_sc}")
            data_analyzed['Sentiment_Score'] = 50

        # ---------------- Candlestick patterns (Kode Anda yang sudah benar) ----------------
        try:
            op = pd.to_numeric(data_analyzed['Open'], errors='coerce').fillna(method='ffill').fillna(0).values
            hi = pd.to_numeric(data_analyzed['High'], errors='coerce').fillna(method='ffill').fillna(0).values
            lo = pd.to_numeric(data_analyzed['Low'], errors='coerce').fillna(method='ffill').fillna(0).values
            cl = pd.to_numeric(data_analyzed['Close'], errors='coerce').fillna(method='ffill').fillna(0).values

            cdl_default_cols = ['CDL_HAMMER','CDL_SHOOTINGSTAR','CDL_DOJI','CDL_ENGULFING','CDL_MORNINGSTAR','CDL_EVENINGSTAR']
            for c in cdl_default_cols:
                if c not in data_analyzed.columns:
                    data_analyzed[c] = 0

            if talib is not None:
                # gunakan talib jika tersedia
                try:
                    data_analyzed['CDL_HAMMER'] = talib.CDLHAMMER(op, hi, lo, cl)
                    data_analyzed['CDL_SHOOTINGSTAR'] = talib.CDLSHOOTINGSTAR(op, hi, lo, cl)
                    data_analyzed['CDL_DOJI'] = talib.CDLDOJI(op, hi, lo, cl)
                    data_analyzed['CDL_ENGULFING'] = talib.CDLENGULFING(op, hi, lo, cl)
                    data_analyzed['CDL_MORNINGSTAR'] = talib.CDLMORNINGSTAR(op, hi, lo, cl)
                    data_analyzed['CDL_EVENINGSTAR'] = talib.CDLEVENINGSTAR(op, hi, lo, cl)
                except Exception as e_tal:
                    st.warning(f"talib error saat menghitung candlestick: {e_tal}")
            else:
                # Fallback ke pandas_ta atau heuristik
                used_fallback = False
                if pta is not None and hasattr(data_analyzed, 'ta'):
                    try:
                        try:
                            data_analyzed = data_analyzed.ta.cdl_pattern(name="all", append=True)
                            used_fallback = True
                        except Exception:
                            raise
                    except Exception as e_pdat:
                        st.info(f"pandas_ta fallback gagal: {e_pdat} — akan gunakan heuristik internal.")
                        used_fallback = False

                if not used_fallback:
                    # Heuristik internal (vectorized)
                    try:
                        data_analyzed['CDL_DOJI'] = detect_doji(op, hi, lo, cl)
                        data_analyzed['CDL_HAMMER'] = detect_hammer(op, hi, lo, cl)
                        data_analyzed['CDL_SHOOTINGSTAR'] = detect_shooting_star(op, hi, lo, cl)
                        data_analyzed['CDL_ENGULFING'] = detect_engulfing(op, hi, lo, cl)
                        ms, es = detect_morning_evening_star(op, hi, lo, cl)
                        data_analyzed['CDL_MORNINGSTAR'] = ms
                        data_analyzed['CDL_EVENINGSTAR'] = es
                    except Exception as e_heur:
                        st.warning(f"Gagal menjalankan heuristik candlestick: {e_heur}")
                        traceback.print_exc()

            # Normalisasi: isi NaN -> 0 dan pastikan int
            cdl_cols = [col for col in data_analyzed.columns if col.upper().startswith('CDL_')]
            if not cdl_cols:
                cdl_cols = cdl_default_cols
            for col in cdl_cols:
                data_analyzed[col] = pd.to_numeric(data_analyzed[col], errors='coerce').fillna(0).astype(int)

        except Exception as e_cdl:
            st.warning(f"Gagal menghitung Candlestick Patterns (V10.1): {e_cdl}")
            traceback.print_exc()
            for c in cdl_default_cols:
                if c not in data_analyzed.columns:
                    data_analyzed[c] = 0
        # -----------------------------------------------------

        if data_analyzed.empty:
            st.warning(f"Data untuk {ticker} kosong setelah analisis.")
            return None

        return data_analyzed

    except Exception as e:
        st.error(f"Error saat menganalisis {ticker}: {e}")
        traceback.print_exc()
        return None
