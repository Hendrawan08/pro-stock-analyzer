# watchlist_tracker.py
import streamlit as st
import pandas as pd
from sqlalchemy.exc import IntegrityError # Untuk mendeteksi duplikat

# --- FUNGSI HELPER BARU V4.1 ---
# FUNGSI INI SEKARANG HANYA MENGHUBUNGKAN, TIDAK MEMBUAT TABEL
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
        # Jika koneksi gagal, tampilkan error dan hentikan
        st.error(f"FATAL: Gagal terhubung ke database. Cek 'Secrets' Anda. Error: {e}")
        st.stop()
# -------------------------------------

class WatchlistTracker:
    
    def __init__(self):
        """
        Versi 4.1: Menggunakan fungsi koneksi global (get_watchlist_connection)
        """
        # 1. Panggil fungsi global yang di-cache
        self.conn = get_watchlist_connection()
            
    # --- PERBAIKAN V4.2 DI SINI ---
    @st.cache_data(ttl=60, show_spinner="Mengambil data watchlist...")
    def get_watchlist(_self) -> list: # <-- 'self' diubah menjadi '_self'
        """Mengambil daftar ticker dari database."""
        # '_self' digunakan untuk mengakses koneksi
        df = _self.conn.query("SELECT symbol FROM watchlist ORDER BY symbol ASC;") 
        return df['symbol'].tolist()
    # ------------------------------

    def add_to_watchlist(self, symbol: str):
        """Menambahkan ticker baru ke database."""
        # Fungsi ini tidak di-cache, jadi 'self' tetap aman
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
        # Fungsi ini tidak di-cache, jadi 'self' tetap aman
        symbol = symbol.upper()
        with self.conn.session as s:
            s.execute(st.text("DELETE FROM watchlist WHERE symbol = :symbol;"), 
                      params=dict(symbol=symbol))
            s.commit()
        self.get_watchlist.clear() # Hapus cache
        st.toast(f"🗑️ {symbol} dihapus dari Watchlist.")
        st.rerun()
        