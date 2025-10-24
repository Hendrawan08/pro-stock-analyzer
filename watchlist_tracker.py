# watchlist_tracker.py
import streamlit as st
import pandas as pd

class WatchlistTracker:
    
    # Kunci session state untuk menyimpan daftar watchlist
    WATCHLIST_KEY = "stock_watchlist"

    def __init__(self):
        # Inisialisasi watchlist di session state jika belum ada
        if self.WATCHLIST_KEY not in st.session_state:
            st.session_state[self.WATCHLIST_KEY] = []
            
    def get_watchlist(self) -> list:
        """Mengambil daftar ticker dari session state."""
        return st.session_state[self.WATCHLIST_KEY]

    def add_to_watchlist(self, symbol: str):
        """Menambahkan ticker baru ke watchlist jika belum ada."""
        symbol = symbol.upper()
        current_list = self.get_watchlist()
        if symbol and symbol not in current_list:
            st.session_state[self.WATCHLIST_KEY].append(symbol)
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
            st.toast(f"🗑️ {symbol} dihapus dari Watchlist.")
            st.rerun()
