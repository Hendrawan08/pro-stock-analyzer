# data/data_manager.py

import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Optional

# Ubah definisi kelas DataManager
class DataManager:
    def __init__(self, ticker, period, interval):
        # Hapus self.ticker, self.period, self.interval
        # Kita akan meneruskannya langsung di fetch_data untuk cache yang lebih baik
        pass 

    # UBAH TANDA TANGAN FUNGSI UNTUK MENERIMA ARGUMEN EKSPILISIT
    @st.cache_data(ttl=3600, show_spinner="Mengambil data dari Yahoo Finance...")
    def fetch_data(_self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        """Mengambil data historis dari Yahoo Finance."""
        try:
            # Gunakan argumen yang diteruskan
            data = yf.download(ticker, period=period, 
                                 interval=interval, progress=False)
            
            if data.empty:
                st.error(f"❌ Error: Data kosong untuk {ticker}. Coba ganti periode.")
                return None
                
            # LOGIKA PEMAKSAAN NAMA KOLOM STANDAR (DIJAGA UNTUK STABILITAS)
            if isinstance(data.columns, pd.MultiIndex):
                # Meratakan kolom seperti ('Close', 'BBCA.JK') menjadi 'Close'
                data.columns = [col[0] for col in data.columns.values]
                
            # Ganti 'Adj Close' menjadi 'Close' jika ada
            if 'Adj Close' in data.columns and 'Close' not in data.columns:
                 data = data.rename(columns={'Adj Close': 'Close'})
            
            # Filter dan validasi kolom yang dibutuhkan
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in data.columns:
                    st.error(f"❌ Error: Kolom '{col}' tidak ditemukan dalam data yfinance untuk ticker {ticker}. Coba interval/periode lain.")
                    return None
                    
            data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            # ==========================================================
            # PERBAIKAN ZONA WAKTU (WIB)
            # ==========================================================
            try:
                # Coba konversi jika data punya timezone (misal, data 1m sering dalam UTC)
                data.index = data.index.tz_convert('Asia/Jakarta')
            except TypeError:
                # Jika data "naive" (tidak punya timezone, misal data 1d),
                # kita asumsikan itu sudah waktu JKT dan kita lokalkan.
                try:
                    data.index = data.index.tz_localize('Asia/Jakarta', ambiguous='infer')
                except Exception as e_localize:
                    st.warning(f"Gagal memproses zona waktu: {e_localize}")
            # ==========================================================

            return data
            
        except Exception as e:
            st.exception(f"❌ Gagal mengambil data: {e}")
            return None