# portfolio_tracker.py
import streamlit as st
import pandas as pd

class PortfolioTracker:
    
    # Kunci session state untuk menyimpan data portofolio
    PORTFOLIO_KEY = "portfolio_holdings"

    def __init__(self):
        # Inisialisasi portofolio di session state jika belum ada
        if self.PORTFOLIO_KEY not in st.session_state:
            st.session_state[self.PORTFOLIO_KEY] = []
            
    def get_holdings(self):
        """Mengambil daftar holdings dari session state."""
        return st.session_state[self.PORTFOLIO_KEY]

    def add_holding(self, symbol: str, buy_price: float, quantity: int):
        """Menambahkan holding baru ke portofolio."""
        new_holding = {
            "symbol": symbol.upper(),
            "buy_price": buy_price,
            "quantity": quantity
        }
        st.session_state[self.PORTFOLIO_KEY].append(new_holding)
        
    def remove_holding(self, index: int):
        """Menghapus holding berdasarkan indeks."""
        if 0 <= index < len(st.session_state[self.PORTFOLIO_KEY]):
            del st.session_state[self.PORTFOLIO_KEY][index]
            
    def update_holding(self, index: int, symbol: str, buy_price: float, quantity: int):
        """Memperbarui holding berdasarkan indeks."""
        if 0 <= index < len(st.session_state[self.PORTFOLIO_KEY]):
            st.session_state[self.PORTFOLIO_KEY][index] = {
                "symbol": symbol.upper(),
                "buy_price": buy_price,
                "quantity": quantity
            }
            
    def calculate_portfolio_metrics(self, holdings: list, current_price_dict: dict) -> tuple[pd.DataFrame, dict]:
        """
        FUNGSI BARU: Hanya menghitung metrik, tidak menampilkan apa-apa.
        Mengembalikan DataFrame dan Kamus (dictionary) berisi total.
        """
        
        if not holdings:
            return pd.DataFrame(), {} # Kembalikan data kosong

        df_holdings = pd.DataFrame(holdings)
        
        # Inisialisasi data untuk PnL
        df_holdings['Current Price'] = 0.0
        df_holdings['Initial Cost'] = df_holdings['buy_price'] * df_holdings['quantity']
        
        # Hitung PnL
        for symbol, price in current_price_dict.items():
            df_holdings.loc[df_holdings['symbol'] == symbol, 'Current Price'] = price
        
        df_holdings['Value'] = df_holdings['Current Price'] * df_holdings['quantity']
        df_holdings['PnL (Rp)'] = df_holdings['Value'] - df_holdings['Initial Cost']
        
        # Tambahkan pencegahan error 'division by zero'
        df_holdings['PnL (%)'] = 0.0
        df_holdings.loc[df_holdings['Initial Cost'] > 0, 'PnL (%)'] = \
            (df_holdings['PnL (Rp)'] / df_holdings['Initial Cost']) * 100
        
        # Ringkasan Total
        total_value = df_holdings['Value'].sum()
        total_cost = df_holdings['Initial Cost'].sum()
        total_pnl_rp = total_value - total_cost
        total_pnl_pct = (total_pnl_rp / total_cost) * 100 if total_cost > 0 else 0

        totals = {
            "cost": total_cost,
            "value": total_value,
            "pnl_rp": total_pnl_rp,
            "pnl_pct": total_pnl_pct
        }
        
        return df_holdings, totals