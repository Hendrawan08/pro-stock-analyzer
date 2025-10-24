# watchlist_tracker.py
import streamlit as st
import pandas as pd
from sqlalchemy.exc import IntegrityError # Untuk mendeteksi duplikat

# --- FUNGSI HELPER BARU V4.0 ---
# SATU FUNGSI UNTUK MENGATUR SEMUANYA
@st.cache_resource(show_spinner="Menghubungkan ke database watchlist...")
def get_watchlist_connection():
    """
    Membuat koneksi ke DB dan setup tabel watchlist.
    Ini akan di-cache dan hanya berjalan sekali.
    """
    conn = st.connection("supabase_db", type="sql")
    
    with conn.session as s:
        s.execute(st.text("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL UNIQUE
            );
        """))
        s.commit()
    return conn
# -------------------------------------

class WatchlistTracker:
    
    def __init__(self):
        """
        Versi 4.0: Menggunakan fungsi koneksi global (get_watchlist_connection)
        untuk menghindari bug __init__ dan cache.
        """
        try:
            # 1. Panggil fungsi global yang di-cache
            self.conn = get_watchlist_connection()
            
        except Exception as e:
            # Error sekarang akan ditangkap di sini jika koneksi gagal
            st.error(f"FATAL: Gagal terhubung ke database Watchlist. Cek 'Secrets' Anda. Error: {e}")
            st.stop()
            
    @st.cache_data(ttl=60, show_spinner="Mengambil data watchlist...")
    def get_watchlist(self) -> list:
        """Mengambil daftar ticker dari database."""
        # Fungsi ini tidak perlu diubah
        df = self.conn.query("SELECT symbol FROM watchlist ORDER BY symbol ASC;")
        return df['symbol'].tolist()

    def add_to_watchlist(self, symbol: str):
        """Menambahkan ticker baru ke database."""
        # Fungsi ini tidak perlu diubah
        symbol = symbol.upper()
        if not symbol:
            st.toast("⚠️ Simbol tidak boleh kosong.")
            return

        try:
            with self.conn.session as s:
                s.execute(st.text("INSERT INTO watchlist (symbol) VALUES (:symbol);"), 
                          params=dict(symbol=symbol))
                s.commit()
            self.get_watchlist.clear() # Hapus cache
            st.toast(f"✅ {symbol} ditambahkan ke Watchlist.")
            st.rerun()
            
        except IntegrityError:
            st.toast(f"⚠️ {symbol} sudah ada di Watchlist.")
        except Exception as e:
            st.error(f"Gagal menambahkan {symbol}: {e}")
        
    def remove_from_watchlist(self, symbol: str):
        """Menghapus ticker dari database."""
        # Fungsi ini tidak perlu diubah
        symbol = symbol.upper()
        with self.conn.session as s:
            s.execute(st.text("DELETE FROM watchlist WHERE symbol = :symbol;"), 
                      params=dict(symbol=symbol))
            s.commit()
        self.get_watchlist.clear() # Hapus cache
        st.toast(f"🗑️ {symbol} dihapus dari Watchlist.")
        st.rerun()

