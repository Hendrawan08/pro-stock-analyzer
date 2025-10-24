# watchlist_tracker.py
import streamlit as st
import pandas as pd
# --- PERBAIKAN V4.3: Impor 'text' dari sqlalchemy ---
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text 

# --- FUNGSI HELPER V4.1 ---
@st.cache_resource(show_spinner="Menghubungkan ke database watchlist...")
def get_watchlist_connection():
    """
    Hanya membuat koneksi ke DB. 
    Tabel diasumsikan sudah ada (dibuat manual di Supabase).
    """
    try:
        conn = st.connection("supabase_db", type="sql")
        return conn
    except Exception as e:
        st.error(f"FATAL: Gagal terhubung ke database. Cek 'Secrets' Anda. Error: {e}")
        st.stop()
# -------------------------------------

class WatchlistTracker:
    
    def __init__(self):
        self.conn = get_watchlist_connection()
            
    @st.cache_data(ttl=60, show_spinner="Mengambil data watchlist...")
    def get_watchlist(_self) -> list:
        df = _self.conn.query("SELECT symbol FROM watchlist ORDER BY symbol ASC;") 
        return df['symbol'].tolist()

    def add_to_watchlist(self, symbol: str):
        symbol = symbol.upper()
        if not symbol:
            st.toast("⚠️ Simbol tidak boleh kosong.")
            return

        try:
            with self.conn.session as s:
                # --- PERBAIKAN V4.3: Menggunakan text() BUKAN st.text() ---
                s.execute(text("INSERT INTO watchlist (symbol) VALUES (:symbol);"), 
                          params=dict(symbol=symbol))
                s.commit()
            self.get_watchlist.clear()
            st.toast(f"✅ {symbol} ditambahkan ke Watchlist.")
            st.rerun()
            
        except IntegrityError:
            st.toast(f"⚠️ {symbol} sudah ada di Watchlist.")
        except Exception as e:
            st.error(f"Gagal menambahkan {symbol}: {e}")
        
    def remove_from_watchlist(self, symbol: str):
        symbol = symbol.upper()
        with self.conn.session as s:
            # --- PERBAIKAN V4.3: Menggunakan text() BUKAN st.text() ---
            s.execute(text("DELETE FROM watchlist WHERE symbol = :symbol;"), 
                      params=dict(symbol=symbol))
            s.commit()
        self.get_watchlist.clear()
        st.toast(f"🗑️ {symbol} dihapus dari Watchlist.")
        st.rerun()

