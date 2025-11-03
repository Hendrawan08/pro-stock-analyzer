# data/data_manager.py

import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Optional

# --- PERBAIKAN V7.2: Menghapus 'class DataManager' yang tidak perlu ---
# Fungsi ini sekarang berdiri sendiri dan caching-nya aman.

@st.cache_data(ttl=3600, show_spinner="Mengambil data dari Yahoo Finance...")
def fetch_data(ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
    """Mengambil data historis dari Yahoo Finance."""
    try:
        data = yf.download(ticker, period=period, 
                             interval=interval, progress=False)
        
        if data.empty:
            st.error(f"❌ Error: Data kosong untuk {ticker}. Coba ganti periode.")
            return None
            
        # Logika pemaksaan nama kolom standar
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns.values]
            
        if 'Adj Close' in data.columns and 'Close' not in data.columns:
             data = data.rename(columns={'Adj Close': 'Close'})
        
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in data.columns:
                st.error(f"❌ Error: Kolom '{col}' tidak ditemukan dalam data yfinance untuk ticker {ticker}. Coba interval/periode lain.")
                return None
                
        data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Perbaikan Zona Waktu (WIB)
        try:
            data.index = data.index.tz_convert('Asia/Jakarta')
        except TypeError:
            try:
                data.index = data.index.tz_localize('Asia/Jakarta', ambiguous='infer')
            except Exception as e_localize:
                st.warning(f"Gagal memproses zona waktu: {e_localize}")

        return data
        
    except Exception as e:
        st.exception(f"❌ Gagal mengambil data: {e}")
        return None