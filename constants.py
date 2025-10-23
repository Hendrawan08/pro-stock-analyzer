# constants.py

import pandas as pd

# Pengaturan API
TICKER_DEFAULT = "BBCA.JK"
PERIOD_DEFAULT = "6mo"
INTERVAL_DEFAULT = "1d"

# Parameter Indikator
# PERBAIKAN: Mengubah 'long' dari 50 menjadi 100 agar berbeda dari 'medium'
MA_CONFIG = {"short": 20, "medium": 50, "long": 100} 
RSI_WINDOW = 14
# TAMBAHKAN KONSTANTA MACD
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
# ---
BB_WINDOW = 20
STOCH_K = 14
STOCH_D = 3

# Ambang Batas Sinyal
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
STOCH_OVERBOUGHT = 80
STOCH_OVERSOLD = 20

# Parameter Pola
# PERBAIKAN: Mengubah default distance dari 5 ke 30 (untuk data harian)
# Logika dinamis akan ditambahkan di reversal_patterns.py
PATTERN_DISTANCE: int = 30 
PATTERN_THRESHOLD: float = 0.02
PATTERN_REVERSAL_FACTOR: float = 0.03

# Konfigurasi Notifikasi
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

# Logika Backtesting
COMMISSION = 0.001