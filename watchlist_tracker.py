# watchlist_tracker.py
import streamlit as st
import pandas as pd
from sqlalchemy.exc import IntegrityError # Untuk mendeteksi duplikat

class WatchlistTracker:
    
    # KUNCI BARU: Nama koneksi di Streamlit Secrets
    DB_CONNECTION_NAME = "supabase_db"

    def __init__(self):
        """
        Versi 3.0: Terhubung ke database SQL (Supabase)
        bukan lagi st.session_state.
        """
        try:
            # 1. Buat koneksi ke database
            self.conn = st.connection(self.DB_CONNECTION_NAME, type="sql")
            
            # 2. Buat tabel jika belum ada (hanya berjalan sekali)
            self._setup_database()
            
        except Exception as e:
            st.error(f"FATAL: Gagal terhubung ke database Watchlist. Cek 'Secrets' Anda. Error: {e}")
            st.stop()
            
    @st.cache_resource(show_spinner="Menyiapkan database watchlist...")
    def _setup_database(_self):
        """Membuat tabel 'watchlist' jika belum ada."""
        with _self.conn.session as s:
            s.execute(st.text("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL UNIQUE
                );
            """))
            s.commit()

    @st.cache_data(ttl=60, show_spinner="Mengambil data watchlist...")
    def get_watchlist(self) -> list:
        """Mengambil daftar ticker dari database."""
        df = self.conn.query("SELECT symbol FROM watchlist ORDER BY symbol ASC;")
        # Konversi DataFrame kolom ke list
        return df['symbol'].tolist()

    def add_to_watchlist(self, symbol: str):
        """Menambahkan ticker baru ke database."""
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
            # Ini terjadi jika 'UNIQUE' constraint gagal (data sudah ada)
            st.toast(f"⚠️ {symbol} sudah ada di Watchlist.")
        except Exception as e:
            st.error(f"Gagal menambahkan {symbol}: {e}")
        
    def remove_from_watchlist(self, symbol: str):
        """Menghapus ticker dari database."""
        symbol = symbol.upper()
        with self.conn.session as s:
            s.execute(st.text("DELETE FROM watchlist WHERE symbol = :symbol;"), 
                      params=dict(symbol=symbol))
            s.commit()
        self.get_watchlist.clear() # Hapus cache
        st.toast(f"🗑️ {symbol} dihapus dari Watchlist.")
        st.rerun()

