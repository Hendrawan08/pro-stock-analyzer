# portfolio_tracker.py
import streamlit as st
import pandas as pd

# --- FUNGSI HELPER (DI LUAR CLASS) ---
# Ini adalah perbaikan V3.1. Fungsi setup dipindah ke luar class
# untuk memperbaiki bug decorator @st.cache_resource.
@st.cache_resource(show_spinner="Menyiapkan database portofolio...")
def _setup_portfolio_database(conn):
    """Membuat tabel 'portfolio' jika belum ada."""
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
# -------------------------------------

class PortfolioTracker:
    
    # KUNCI BARU: Nama koneksi di Streamlit Secrets
    DB_CONNECTION_NAME = "supabase_db"

    def __init__(self):
        """
        Versi 3.1: Memperbaiki bug cache decorator.
        """
        try:
            # 1. Buat koneksi
            conn = st.connection(self.DB_CONNECTION_NAME, type="sql")
            
            # 2. Panggil helper setup (eksternal)
            _setup_portfolio_database(conn)
            
            # 3. Simpan koneksi di instance
            self.conn = conn
            
        except Exception as e:
            st.error(f"FATAL: Gagal terhubung ke database Portofolio. Cek 'Secrets' Anda. Error: {e}")
            st.stop()
            
    @st.cache_data(ttl=60, show_spinner="Mengambil data portofolio...")
    def get_holdings(self) -> list:
        """Mengambil daftar holdings dari database."""
        df = self.conn.query("SELECT * FROM portfolio ORDER BY id ASC;")
        # Konversi DataFrame ke format list-of-dict yang diharapkan app.py
        return df.to_dict('records')

    def add_holding(self, symbol: str, buy_price: float, quantity: int):
        """Menambahkan holding baru ke database."""
        with self.conn.session as s:
            s.execute(st.text("""
                INSERT INTO portfolio (symbol, buy_price, quantity) 
                VALUES (:symbol, :buy_price, :quantity);
            """), params=dict(symbol=symbol.upper(), buy_price=buy_price, quantity=quantity))
            s.commit()
        # Hapus cache agar data baru langsung muncul
        self.get_holdings.clear()
        
    def remove_holding(self, index: int):
        """Menghapus holding berdasarkan indeks (mengambil ID dari list)."""
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
        
        for symbol, price in current_price_dict.items():
            df_holdings.loc[df_holdings['symbol'] == symbol, 'Current Price'] = price
        
        df_holdings['Value'] = df_holdings['Current Price'] * df_holdings['quantity']
        df_holdings['PnL (Rp)'] = df_holdings['Value'] - df_holdings['Initial Cost']
        
        df_holdings['PnL (%)'] = 0.0
        df_holdings.loc[df_holdings['Initial Cost'] > 0, 'PnL (%)'] = \
            (df_holdings['PnL (Rp)'] / df_holdings['Initial Cost']) * 100
        
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

