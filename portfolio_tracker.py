# portfolio_tracker.py
import streamlit as st
import pandas as pd
from sqlalchemy import text  # <-- PERBAIKAN V4.3: Impor 'text' dari sqlalchemy

# --- FUNGSI HELPER V4.1 ---
@st.cache_resource(show_spinner="Menghubungkan ke database portofolio...")
def get_portfolio_connection():
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

class PortfolioTracker:
    
    def __init__(self):
        self.conn = get_portfolio_connection()
            
    @st.cache_data(ttl=60, show_spinner="Mengambil data portofolio...")
    def get_holdings(_self) -> list: 
        df = _self.conn.query("SELECT * FROM portfolio ORDER BY id ASC;")
        return df.to_dict('records')

    def add_holding(self, symbol: str, buy_price: float, quantity: int):
        with self.conn.session as s:
            # --- PERBAIKAN V4.3: Menggunakan text() BUKAN st.text() ---
            s.execute(text("""
                INSERT INTO portfolio (symbol, buy_price, quantity) 
                VALUES (:symbol, :buy_price, :quantity);
            """), params=dict(symbol=symbol.upper(), buy_price=buy_price, quantity=quantity))
            s.commit()
        self.get_holdings.clear()
        
    def remove_holding(self, index: int):
        holdings = self.get_holdings()
        
        if 0 <= index < len(holdings):
            item_id_to_delete = holdings[index]['id']
            with self.conn.session as s:
                # --- PERBAIKAN V4.3: Menggunakan text() BUKAN st.text() ---
                s.execute(text("DELETE FROM portfolio WHERE id = :id;"), 
                          params=dict(id=item_id_to_delete))
                s.commit()
            self.get_holdings.clear()
            
    def update_holding(self, index: int, symbol: str, buy_price: float, quantity: int):
        holdings = self.get_holdings()
        
        if 0 <= index < len(holdings):
            item_id_to_update = holdings[index]['id']
            
            with self.conn.session as s:
                # --- PERBAIKAN V4.3: Menggunakan text() BUKAN st.text() ---
                s.execute(text("""
                    UPDATE portfolio 
                    SET symbol = :symbol, buy_price = :buy_price, quantity = :quantity
                    WHERE id = :id;
                """), params=dict(
                    symbol=symbol.upper(), 
                    buy_price=buy_price, 
                    quantity=quantity,
                    id=item_id_to_update
                ))
                s.commit()
            self.get_holdings.clear()
            
    def calculate_portfolio_metrics(self, holdings: list, current_price_dict: dict) -> tuple[pd.DataFrame, dict]:
        # ... (Tidak ada perubahan di fungsi kalkulator) ...
        if not holdings:
            return pd.DataFrame(), {}
        df_holdings = pd.DataFrame(holdings)
        df_holdings['Current Price'] = 0.0
        df_holdings['Initial Cost'] = df_holdings['buy_price'] * df_holdings['quantity']
        df_holdings['Value'] = 0.0
        for symbol, price in current_price_dict.items():
            df_holdings.loc[df_holdings['symbol'] == symbol, 'Current Price'] = price
        df_holdings['Value'] = df_holdings['Current Price'] * df_holdings['quantity']
        df_holdings['PnL (Rp)'] = df_holdings['Value'] - df_holdings['Initial Cost']
        df_holdings['PnL (%)'] = 0.0
        mask_cost_not_zero = df_holdings['Initial Cost'] != 0
        df_holdings.loc[mask_cost_not_zero, 'PnL (%)'] = \
            (df_holdings.loc[mask_cost_not_zero, 'PnL (Rp)'] / df_holdings.loc[mask_cost_not_zero, 'Initial Cost']) * 100
        total_value = df_holdings['Value'].sum()
        total_cost = df_holdings['Initial Cost'].sum()
        total_pnl_rp = total_value - total_cost
        total_pnl_pct = (total_pnl_rp / total_cost) * 100 if total_cost != 0 else 0
        totals = {
            "cost": total_cost,
            "value": total_value,
            "pnl_rp": total_pnl_rp,
            "pnl_pct": total_pnl_pct
        }
        return df_holdings, totals

