# analysis/analyzer.py
import pandas as pd
import streamlit as st
from data.data_manager import DataManager
from indicators.moving_average import MovingAverage
from indicators.rsi import RSI
from indicators.macd import MACD
from indicators.bollinger_bands import BollingerBands
from indicators.stochastic import Stochastic
from patterns.reversal_patterns import ReversalPatterns

# Gunakan cache_data di sini, BUKAN di app.py
@st.cache_data(ttl=600)
def fetch_and_analyze_data(ticker, period, interval):
    """
    Fungsi inti: Mengambil data dan menjalankan semua analisis indikator.
    Fungsi ini sekarang terpusat dan bisa dipakai di semua halaman.
    """
    data_manager = DataManager(None, None, None) 
    
    # 1. Ambil Data
    data = data_manager.fetch_data(ticker, period, interval) 
    if data is None:
        return None
        
    # 2. Hitung Semua Indikator (Rangkaian)
    # Kita tambahkan try-except untuk keamanan saat scanning
    try:
        data = MovingAverage().calculate(data)
        data = RSI().calculate(data)
        data = MACD().calculate(data)
        data = BollingerBands().calculate(data)
        data = Stochastic().calculate(data)
        data = ReversalPatterns().detect_all(data, interval)
        
        # Hapus NaN setelah semua perhitungan
        analyzed_data = data.dropna()
        
        if analyzed_data.empty:
            return None
            
        return analyzed_data
        
    except Exception as e:
        # Saat scanning, kita tidak ingin menghentikan program, cukup lewati
        print(f"Error saat menganalisis {ticker}: {e}")
        return None