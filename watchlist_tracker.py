# watchlist_tracker.py
import streamlit as st
import pandas as pd
import os

class WatchlistTracker:
    
    # Kunci session state untuk menyimpan daftar watchlist
    WATCHLIST_KEY = "stock_watchlist"
    FILE_PATH = "watchlist_data.xlsx"  # Nama file penyimpanan Excel

    def __init__(self):
        # Inisialisasi watchlist di session state jika belum ada
        if self.WATCHLIST_KEY not in st.session_state:
            st.session_state[self.WATCHLIST_KEY] = []

    # -----------------------------
    # 🔹 Fungsi Get / Add / Remove
    # -----------------------------
    def get_watchlist(self) -> list:
        """Mengambil daftar ticker dari session state."""
        return st.session_state[self.WATCHLIST_KEY]

    def add_to_watchlist(self, symbol: str):
        """Menambahkan ticker baru ke watchlist jika belum ada."""
        symbol = symbol.upper()
        current_list = self.get_watchlist()
        if symbol and symbol not in current_list:
            st.session_state[self.WATCHLIST_KEY].append(symbol)
            self.save_to_excel()  # ✅ Simpan otomatis setiap kali nambah
            st.toast(f"✅ {symbol} ditambahkan ke Watchlist.")
            st.rerun()
        elif symbol in current_list:
            st.toast(f"⚠️ {symbol} sudah ada di Watchlist.")
        
    def remove_from_watchlist(self, symbol: str):
        """Menghapus ticker dari watchlist."""
        symbol = symbol.upper()
        current_list = self.get_watchlist()
        if symbol in current_list:
            st.session_state[self.WATCHLIST_KEY].remove(symbol)
            self.save_to_excel()  # ✅ Simpan otomatis setiap kali hapus
            st.toast(f"🗑️ {symbol} dihapus dari Watchlist.")
            st.rerun()

    # -----------------------------
    # 💾 Fungsi Simpan & Muat Excel
    # -----------------------------
    def save_to_excel(self):
        """Menyimpan daftar watchlist ke file Excel."""
        try:
            df = pd.DataFrame({"symbol": st.session_state[self.WATCHLIST_KEY]})
            df.to_excel(self.FILE_PATH, index=False)
            st.toast("💾 Watchlist berhasil disimpan ke Excel.")
        except Exception as e:
            st.error(f"❌ Gagal menyimpan watchlist ke Excel: {e}")

    def load_from_excel(self):
        """Memuat watchlist dari file Excel jika ada."""
        if os.path.exists(self.FILE_PATH):
            try:
                df = pd.read_excel(self.FILE_PATH)
                if "symbol" in df.columns:
                    st.session_state[self.WATCHLIST_KEY] = df["symbol"].tolist()
                    st.toast("📂 Watchlist berhasil dimuat dari Excel.")
            except Exception as e:
                st.toast(f"❌ Gagal memuat watchlist dari Excel: {e}")
