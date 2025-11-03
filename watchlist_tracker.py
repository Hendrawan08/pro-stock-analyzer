# watchlist_tracker.py
import streamlit as st
import pandas as pd
import os

class WatchlistTracker:
    
    WATCHLIST_KEY = "stock_watchlist"
    FILE_PATH = "watchlist_data.xlsx"

    def __init__(self, auto_load: bool = True):
        """
        PERBAIKAN V7.6: Menambahkan __init__ yang benar.
        Ini akan menginisialisasi session_state JIKA BELUM ADA,
        dan memanggil load_from_excel() HANYA SEKALI per sesi.
        """
        if self.WATCHLIST_KEY not in st.session_state:
            st.session_state[self.WATCHLIST_KEY] = []
            if auto_load:
                self.load_from_excel()

    # -----------------------------
    # 🔹 Fungsi Get / Add / Remove
    # -----------------------------
    def get_watchlist(self) -> list:
        """PERBAIKAN V7.6: Menggunakan .get() untuk keamanan"""
        return st.session_state.get(self.WATCHLIST_KEY, [])

    def add_to_watchlist(self, symbol: str):
        """Menambahkan ticker baru ke watchlist jika belum ada."""
        symbol = symbol.upper()
        current_list = self.get_watchlist()
        if symbol and symbol not in current_list:
            current_list.append(symbol)
            st.session_state[self.WATCHLIST_KEY] = current_list
            self.save_to_excel()
            st.toast(f"✅ {symbol} ditambahkan ke Watchlist.")
            # st.rerun() # Dihapus di V7.0 (sudah benar)
        elif symbol in current_list:
            st.toast(f"⚠️ {symbol} sudah ada di Watchlist.")
        
    def remove_from_watchlist(self, symbol: str):
        """Menghapus ticker dari watchlist."""
        symbol = symbol.upper()
        current_list = self.get_watchlist()
        if symbol in current_list:
            current_list.remove(symbol)
            st.session_state[self.WATCHLIST_KEY] = current_list
            self.save_to_excel()
            st.toast(f"🗑️ {symbol} dihapus dari Watchlist.")
            # st.rerun() # Dihapus di V7.0 (sudah benar)

    # -----------------------------
    # 💾 Fungsi Simpan & Muat Excel
    # -----------------------------
    def save_to_excel(self):
        """Menyimpan daftar watchlist ke file Excel."""
        try:
            df = pd.DataFrame({"symbol": self.get_watchlist()}) # Gunakan getter
            df.to_excel(self.FILE_PATH, index=False)
            st.toast("💾 Watchlist berhasil disimpan ke Excel.")
        except Exception as e:
            st.error(f"❌ Gagal menyimpan watchlist ke Excel: {e}")

    def load_from_excel(self):
        """
        Memuat watchlist dari file Excel jika ada.
        PERBAIKAN V7.6: Mengembalikan st.toast/st.warning.
        Ini sekarang aman karena __init__ hanya berjalan sekali.
        """
        if not os.path.exists(self.FILE_PATH):
            return
            
        try:
            if os.path.getsize(self.FILE_PATH) == 0:
                return
                
            df = pd.read_excel(self.FILE_PATH)
            df.columns = df.columns.str.lower()
            
            if "symbol" in df.columns:
                st.session_state[self.WATCHLIST_KEY] = df["symbol"].astype(str).str.upper().tolist()
                st.toast("📂 Watchlist berhasil dimuat dari Excel.") # Kembalikan toast
            else:
                st.warning("File watchlist Excel tidak memiliki kolom 'symbol'.") # Kembalikan warning
                
        except Exception as e:
            st.toast(f"❌ Gagal memuat watchlist dari Excel: {e}") # Kembalikan toast
