import pandas as pd
from typing import List, Tuple, Dict

# Impor semua konstanta yang dibutuhkan
from constants import (
    RSI_OVERBOUGHT, RSI_OVERSOLD,
    STOCH_OVERBOUGHT, STOCH_OVERSOLD,
    MA_SHORT_WINDOW, MA_MEDIUM_WINDOW, MA_LONG_WINDOW
)

class SignalGenerator:
    """
    Menghasilkan sinyal trading (Aksi & Tren) dan ringkasan naratif.
    """

    def generate(self, data: pd.DataFrame, ticker: str, interval: str) -> Tuple[List[str], List[str], Dict, str]:
        """
        Menganalisis baris data terakhir untuk sinyal, tren, dan narasi.
        """
        action_signals = []
        trend_signals = []
        narrative_summary = "" # <-- BARU

        if data.empty:
            return action_signals, trend_signals, {}, "Data tidak cukup."
        
        if len(data) < 2:
            last = data.iloc[-1].to_dict()
            prev = last 
        else:
            last = data.iloc[-1].to_dict()
            prev = data.iloc[-2].to_dict()

        # --- 1. Analisis Sinyal Aksi (Jangka Pendek) ---
        if last["RSI"] < RSI_OVERSOLD and prev["RSI"] > RSI_OVERSOLD:
            action_signals.append(f"🟢 RSI baru saja memasuki area Oversold ({last['RSI']:.1f}) - Sinyal Beli Potensial.")
        elif last["RSI"] > RSI_OVERBOUGHT and prev["RSI"] < RSI_OVERBOUGHT:
            action_signals.append(f"🔴 RSI baru saja memasuki area Overbought ({last['RSI']:.1f}) - Sinyal Jual Potensial.")
            
        if last["MACD"] > last["MACD_Signal"] and prev["MACD"] < prev["MACD_Signal"]:
            action_signals.append(f"🟢 MACD Cross Up (Golden Cross) - Sinyal Beli Kuat.")
        elif last["MACD"] < last["MACD_Signal"] and prev["MACD"] > prev["MACD_Signal"]:
            action_signals.append(f"🔴 MACD Cross Down (Death Cross) - Sinyal Jual Kuat.")

        if last["%K"] < STOCH_OVERSOLD and last["%D"] < STOCH_OVERSOLD and last["%K"] > last["%D"]:
             action_signals.append(f"🟢 Stochastic Cross Up di area Oversold - Sinyal Beli.")
        elif last["%K"] > STOCH_OVERBOUGHT and last["%D"] > STOCH_OVERBOUGHT and last["%K"] < last["%D"]:
             action_signals.append(f"🔴 Stochastic Cross Down di area Overbought - Sinyal Jual.")

        engulfing_signal = last.get("CDL_ENGULFING", 0)
        if engulfing_signal == 100: action_signals.append("🟢 Pola Candlestick: Bullish Engulfing Terdeteksi.")
        elif engulfing_signal == -100: action_signals.append("🔴 Pola Candlestick: Bearish Engulfing Terdeteksi.")
        if last.get("CDL_HAMMER", 0) == 100: action_signals.append("🟢 Pola Candlestick: Hammer Terdeteksi (Potensi Reversal Naik).")
        if last.get("CDL_SHOOTINGSTAR", 0) == -100: action_signals.append("🔴 Pola Candlestick: Shooting Star Terdeteksi (Potensi Reversal Turun).")
        if last.get("CDL_DOJI", 0) != 0: action_signals.append("🟡 Pola Candlestick: Doji Terdeteksi (Indikasi Pasar Ragu/Indecision).")
        if last.get("CDL_MORNINGSTAR", 0) == 100: action_signals.append("🟢 Pola Candlestick: Morning Star Terdeteksi (Sinyal Beli Kuat).")
        if last.get("CDL_EVENINGSTAR", 0) == -100: action_signals.append("🔴 Pola Candlestick: Evening Star Terdeteksi (Sinyal Jual Kuat).")
        
        if interval not in ['1m', '5m', '15m']:
            if last.get("DB_Signal", False): action_signals.append(f"🟢 Pola Double Bottom ('W') Terkonfirmasi - Sinyal Beli Jangka Panjang.")
            if last.get("DT_Signal", False): action_signals.append(f"🔴 Pola Double Top ('M') Terkonfirmasi - Sinyal Jual Jangka Panjang.")

        # --- 2. Analisis Konteks Tren (Jangka Panjang) ---
        if last["MA_S"] > last["MA_M"]:
            trend_signals.append(f"📈 Tren Jangka Pendek-Menengah Naik (MA{MA_SHORT_WINDOW} > MA{MA_MEDIUM_WINDOW}).")
        else:
            trend_signals.append(f"📉 Tren Jangka Pendek-Menengah Turun (MA{MA_SHORT_WINDOW} < MA{MA_MEDIUM_WINDOW}).")

        if last["MA_M"] > last["MA_L"]:
            trend_signals.append(f"✨ Tren Jangka Panjang NAIK (MA{MA_MEDIUM_WINDOW} > MA{MA_LONG_WINDOW}).")
            if prev["MA_M"] < prev["MA_L"]: trend_signals.append(f"🚀 MA GOLDEN CROSS BARU SAJA TERJADI!")
        else:
            trend_signals.append(f"💀 Tren Jangka Panjang TURUN (MA{MA_MEDIUM_WINDOW} < MA{MA_LONG_WINDOW}).")
            if prev["MA_M"] > prev["MA_L"]: trend_signals.append(f"☠️ MA DEATH CROSS BARU SAJA TERJADI!")
        
        # --- 3. BUAT RINGKASAN NARATIF (V11.1 - BARU) ---
        try:
            score = last.get("Sentiment_Score", 50)
            
            # Tentukan sentimen utama
            if score >= 70:
                narrative_summary = f"Secara teknikal, {ticker} terlihat **sangat bullish** (Skor {score:.0f}/100)."
            elif score >= 50:
                narrative_summary = f"Secara teknikal, {ticker} berada dalam tren **bullish** (Skor {score:.0f}/100)."
            elif score > 40:
                 narrative_summary = f"Secara teknikal, {ticker} terlihat **netral** (Skor {score:.0f}/100)."
            else:
                narrative_summary = f"Secara teknikal, {ticker} berada dalam tren **bearish** (Skor {score:.0f}/100)."

            # Tambahkan detail pendukung
            if last["MA_M"] > last["MA_L"]:
                narrative_summary += " Tren jangka panjang (MA 50/100) mengkonfirmasi **kenaikan**."
            else:
                 narrative_summary += " Tren jangka panjang (MA 50/100) mengkonfirmasi **penurunan**."
            
            # Tambahkan detail momentum
            if last["RSI"] < RSI_OVERSOLD:
                narrative_summary += " Namun, RSI (<30) menunjukkan kondisi **jenuh jual (oversold)**."
            elif last["RSI"] > RSI_OVERBOUGHT:
                narrative_summary += " Namun, RSI (>70) menunjukkan kondisi **jenuh beli (overbought)**."
            elif (last["MACD"] > last["MACD_Signal"]) and (prev["MACD"] < prev["MACD_Signal"]):
                narrative_summary += " Momentum jangka pendek baru saja **menguat** (MACD Cross Up)."
            elif (last["MACD"] < last["MACD_Signal"]) and (prev["MACD"] > prev["MACD_Signal"]):
                 narrative_summary += " Momentum jangka pendek baru saja **melemah** (MACD Cross Down)."
                 
        except Exception as e:
            print(f"Gagal membuat narasi: {e}")
            narrative_summary = "Gagal membuat ringkasan otomatis."
        # --------------------------------------------------

        return action_signals, trend_signals, last, narrative_summary