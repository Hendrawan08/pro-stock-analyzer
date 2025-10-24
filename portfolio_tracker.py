# portfolio_tracker.py
import streamlit as st
import pandas as pd

# --- FUNGSI HELPER BARU V4.0 ---
# SATU FUNGSI UNTUK MENGATUR SEMUANYA
@st.cache_resource(show_spinner="Menghubungkan ke database portofolio...")
def get_portfolio_connection():
    """
    Membuat koneksi ke DB dan setup tabel portofolio.
    Ini akan di-cache dan hanya berjalan sekali.
    """
    conn = st.connection("supabase_db", type="sql")
    
    with conn.session as s:
        s.execute(st.text("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                buy_price FLOAT NOT NULL,
                quantity INTEGER NOT NULL
            );
        """))
        s.commit()
    return conn
# -------------------------------------

class PortfolioTracker:
    
    def __init__(self):
        """
        Versi 4.0: Menggunakan fungsi koneksi global (get_portfolio_connection)
        untuk menghindari bug __init__ dan cache.
        """
        try:
            # 1. Panggil fungsi global yang di-cache
            self.conn = get_portfolio_connection()
            
        except Exception as e:
            st.error(f"FATAL: Gagal terhubung ke database Portofolio. Cek 'Secrets' Anda. Error: {e}")
            st.stop()
            
    @st.cache_data(ttl=60, show_spinner="Mengambil data portofolio...")
    def get_holdings(self) -> list:
        """Mengambil daftar holdings dari database."""
        # Fungsi ini tidak perlu diubah
        df = self.conn.query("SELECT * FROM portfolio ORDER BY id ASC;")
        return df.to_dict('records')

    def add_holding(self, symbol: str, buy_price: float, quantity: int):
        """Menambahkan holding baru ke database."""
        # Fungsi ini tidak perlu diubah
        with self.conn.session as s:
            s.execute(st.text("""
                INSERT INTO portfolio (symbol, buy_price, quantity) 
                VALUES (:symbol, :buy_price, :quantity);
            """), params=dict(symbol=symbol.upper(), buy_price=buy_price, quantity=quantity))
            s.commit()
        self.get_holdings.clear()
        
    def remove_holding(self, index: int):
        """Menghapus holding berdasarkan indeks (mengambil ID dari list)."""
        # Fungsi ini tidak perlu diubah
        holdings = self.get_holdings()
        
        if 0 <= index < len(holdings):
            item_id_to_delete = holdings[index]['id']
            with self.conn.session as s:
                s.execute(st.text("DELETE FROM portfolio WHERE id = :id;"), 
                          params=dict(id=item_id_to_delete))
                s.commit()
            self.get_holdings.clear()
            
    def update_holding(self, index: int, symbol: str, buy_price: float, quantity: int):
        """Memperbarui holding berdasarkan indeks (mengambil ID dari list)."""
        # Fungsi ini tidak perlu diubah
        holdings = self.get_holdings()
        
        if 0 <= index < len(holdings):
            item_id_to_update = holdings[index]['id']
            
            with self.conn.session as s:
                s.execute(st.text("""
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
        """
        Fungsi ini tidak berubah, hanya kalkulator.
        """
        
        if not holdings:
            return pd.DataFrame(), {}

        df_holdings = pd.DataFrame(holdings)
        df_holdings['Current Price'] = 0.0
        df_holdings['Initial Cost'] = df_holdings['buy_price'] * df_holdings['quantity']
        
        # Inisialisasi kolom 'Value' sebelum loop
        df_holdings['Value'] = 0.0

        for symbol, price in current_price_dict.items():
            df_holdings.loc[df_holdings['symbol'] == symbol, 'Current Price'] = price
        
        # Hitung 'Value' setelah 'Current Price' diisi
        df_holdings['Value'] = df_holdings['Current Price'] * df_holdings['quantity']
        df_holdings['PnL (Rp)'] = df_holdings['Value'] - df_holdings['Initial Cost']
        
        df_holdings['PnL (%)'] = 0.0
        # Periksa Initial Cost != 0 sebelum dibagi
        mask_cost_not_zero = df_holdings['Initial Cost'] != 0
        df_holdings.loc[mask_cost_not_zero, 'PnL (%)'] = \
            (df_holdings.loc[mask_cost_not_zero, 'PnL (Rp)'] / df_holdings.loc[mask_cost_not_zero, 'Initial Cost']) * 100
        
        total_value = df_holdings['Value'].sum()
        total_cost = df_holdings['Initial Cost'].sum()
        total_pnl_rp = total_value - total_cost
        
        # Periksa total_cost != 0 sebelum dibagi
        total_pnl_pct = (total_pnl_rp / total_cost) * 100 if total_cost != 0 else 0

        totals = {
            "cost": total_cost,
            "value": total_value,
            "pnl_rp": total_pnl_rp,
            "pnl_pct": total_pnl_pct
        }
        
        return df_holdings, totals

