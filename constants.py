# constants.py

# --- Ticker Default ---
TICKER_DEFAULT = "BBCA.JK"

# --- Periode Moving Average (MA) ---
MA_SHORT_WINDOW = 20
MA_MEDIUM_WINDOW = 50
MA_LONG_WINDOW = 100

# --- Periode RSI ---
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# --- Periode MACD ---
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# --- Periode Bollinger Bands ---
BOLLINGER_WINDOW = 20
BOLLINGER_STD = 2

# --- Periode Stochastic ---
STOCHASTIC_K = 14
STOCHASTIC_D = 3
STOCHASTIC_SMOOTH_K = 3
# --- TAMBAHKAN DUA BARIS INI ---
STOCH_OVERBOUGHT = 80
STOCH_OVERSOLD = 20
# -------------------------------

# --- Pola Reversal ---
REVERSAL_PATTERN_WINDOW = 20 # Jendela untuk mencari Puncak/Lembah

# --- Backtester ---
COMMISSION = 0.0025 # Biaya komisi per transaksi (misal: 0.25%)