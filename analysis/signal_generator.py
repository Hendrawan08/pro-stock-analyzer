import pandas as pd
from typing import List, Tuple
from constants import *
# import requests # Untuk notifikasi Telegram

class SignalGenerator:
    
    def __init__(self):
        self.last_signal_time = None 

    def _send_telegram_notification(self, message: str):
        # Logika Notifikasi (tidak diubah)
        pass

    # ==========================================================
    # PERBAIKAN: Tambahkan 'interval: str' sebagai argumen
    # ==========================================================
    def generate(self, data: pd.DataFrame, ticker: str, interval: str) -> Tuple[List[str], List[str], pd.Series]:
        """
        Menghasilkan sinyal dan ringkasan tren, 
        dipisahkan menjadi Sinyal Aksi dan Konteks Tren.
        """
        
        last = data.iloc[-1]
        action_signals: List[str] = [] # Untuk sinyal Beli/Jual
        trend_signals: List[str] = []  # Untuk sinyal Konteks/Status
        
        is_buy_signal = False
        is_sell_signal = False

        # --- 1. Analisis MACD Crossover ---
        if last["MACD"] > last["MACD_Signal"] and last["MACD_Hist"] > 0:
            action_signals.append("🟢 MACD Cross Up di atas 0 → Sinyal **BUY Kuat** (Momentum Positif)")
            is_buy_signal = True
        elif last["MACD"] > last["MACD_Signal"]:
            action_signals.append("🟡 MACD Cross Up → Sinyal **BUY** (Momentum Awal)")
            is_buy_signal = True
        elif last["MACD"] < last["MACD_Signal"] and last["MACD_Hist"] < 0:
            action_signals.append("🔴 MACD Cross Down di bawah 0 → Sinyal **SELL Kuat** (Momentum Negatif)")
            is_sell_signal = True
        else:
            # Ini adalah KONTEKS, bukan AKSI
            trend_signals.append("🔵 MACD → Sideways / Sinyal tidak jelas.")
        
        # --- 2. Analisis RSI ---
        if last["RSI"] < RSI_OVERSOLD:
            action_signals.append(f"🟢 RSI ({last['RSI']:.2f}) < {RSI_OVERSOLD} → **Oversold**, Potensi Rebound.")
            is_buy_signal = True
        elif last["RSI"] > RSI_OVERBOUGHT:
            action_signals.append(f"🔴 RSI ({last['RSI']:.2f}) > {RSI_OVERBOUGHT} → **Overbought**, Potensi Koreksi.")
            is_sell_signal = True
            
        # --- 3. Analisis Stochastic ---
        if last["%K"] < STOCH_OVERSOLD and last["%D"] < STOCH_OVERSOLD and last["%K"] > last["%D"]:
             action_signals.append(f"🟢 Stochastics Cross-Up di area Oversold → Konfirmasi **BUY**.")
             is_buy_signal = True
        elif last["%K"] > STOCH_OVERBOUGHT and last["%D"] > STOCH_OVERBOUGHT and last["%K"] < last["%D"]:
             action_signals.append(f"🔴 Stochastics Cross-Down di area Overbought → Konfirmasi **SELL**.")
             is_sell_signal = True

        # --- 4. Analisis MA (Tren Jangka Panjang) ---
        # Ini adalah KONTEKS, bukan AKSI
        if last["MA_S"] > last["MA_M"] and last["MA_M"] > last["MA_L"]:
            trend_signals.append("✨ Susunan MA (**Golden Cross**) → Tren **Kuat Naik**.")
        elif last["MA_S"] < last["MA_M"] and last["MA_M"] < last["MA_L"]:
            trend_signals.append("💀 Susunan MA (**Death Cross**) → Tren **Kuat Turun**.")
        else:
            trend_signals.append("🌊 Susunan MA tidak teratur → Tren **Sideways**.")

        # --- 5. Analisis Pola (Terbaru) ---
        # (Logika "pintar" ada di 'patterns.py', jadi kita tidak perlu 'if interval' di sini)
        if last["DB_Signal"]:
            action_signals.append("🟢 Pola **Double Bottom** terdeteksi → Potensi Reversal Naik.")
            is_buy_signal = True
        if last["DT_Signal"]:
            action_signals.append("🔴 Pola **Double Top** terdeteksi → Potensi Penurunan Harga.")
            is_sell_signal = True
            
        # --- Notifikasi (Tidak diubah, tapi diperbaiki) ---
        if (is_buy_signal or is_sell_signal) and (self.last_signal_time is None or (pd.Timestamp.now() - self.last_signal_time).seconds > 300):
            # Hanya kirim sinyal aksi
            notif_msg = [s for s in action_signals if "BUY" in s or "SELL" in s] 
            
            if is_buy_signal:
                msg = f"🔔 Sinyal BELI Kuat terdeteksi untuk {ticker}!\nHarga: {last['Close']:.2f}\nSinyal: {', '.join(notif_msg)}"
                self._send_telegram_notification(msg)
                self.last_signal_time = pd.Timestamp.now()
            elif is_sell_signal:
                msg = f"🔔 Sinyal JUAL Kuat terdeteksi untuk {ticker}!\nHarga: {last['Close']:.2f}\nSinyal: {', '.join(notif_msg)}"
                self._send_telegram_notification(msg)
                self.last_signal_time = pd.Timestamp.now()
        
        # PERUBAHAN: Kembalikan KEDUA daftar sinyal
        return action_signals, trend_signals, last
