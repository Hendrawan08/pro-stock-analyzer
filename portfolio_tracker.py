# file: portfolio_tracker.py
import streamlit as st
import pandas as pd
import os
from typing import Tuple, Dict

class PortfolioTracker:
    PORTFOLIO_KEY = "portfolio_holdings"
    EXCEL_FILE = "portfolio_data.xlsx"

    def __init__(self, auto_load: bool = True):
        """
        Inisialisasi tracker.
        - load dari Excel hanya jika session_state belum punya key (hanya sekali per session).
        - auto_load=True akan mencoba load file jika ada.
        """
        if self.PORTFOLIO_KEY not in st.session_state:
            st.session_state[self.PORTFOLIO_KEY] = []
            if auto_load:
                # hanya load sekali saat session_state belum ada
                self.load_from_excel()

    # -------------------------
    # CRUD sederhana + persist
    # -------------------------
    def get_holdings(self):
        return st.session_state[self.PORTFOLIO_KEY]

    def add_holding(self, symbol: str, buy_price: float, quantity: int, auto_save: bool = True):
        new_holding = {
            "symbol": symbol.upper(),
            "buy_price": float(buy_price),
            "quantity": int(quantity)
        }
        st.session_state[self.PORTFOLIO_KEY].append(new_holding)
        if auto_save:
            self._persist_to_excel()

    def remove_holding(self, index: int, auto_save: bool = True):
        if 0 <= index < len(st.session_state[self.PORTFOLIO_KEY]):
            del st.session_state[self.PORTFOLIO_KEY][index]
            if auto_save:
                self._persist_to_excel()
            return True
        return False

    def update_holding(self, index: int, symbol: str, buy_price: float, quantity: int, auto_save: bool = True):
        if 0 <= index < len(st.session_state[self.PORTFOLIO_KEY]):
            st.session_state[self.PORTFOLIO_KEY][index] = {
                "symbol": symbol.upper(),
                "buy_price": float(buy_price),
                "quantity": int(quantity)
            }
            if auto_save:
                self._persist_to_excel()
            return True
        return False

    # -------------------------
    # Perhitungan metrik
    # -------------------------
    def calculate_portfolio_metrics(self, holdings: list, current_price_dict: dict) -> Tuple[pd.DataFrame, Dict]:
        if not holdings:
            return pd.DataFrame(), {}

        df_holdings = pd.DataFrame(holdings)

        # Pastikan kolom numeric valid
        df_holdings['buy_price'] = pd.to_numeric(df_holdings.get('buy_price', 0), errors='coerce').fillna(0.0)
        df_holdings['quantity'] = pd.to_numeric(df_holdings.get('quantity', 0), errors='coerce').fillna(0).astype(int)

        df_holdings['Current Price'] = 0.0
        df_holdings['Initial Cost'] = df_holdings['buy_price'] * df_holdings['quantity']

        # Assign current prices berdasarkan symbol (normalisasi uppercase)
        for symbol, price in current_price_dict.items():
            df_holdings.loc[df_holdings['symbol'].str.upper() == symbol.upper(), 'Current Price'] = float(price or 0.0)

        df_holdings['Value'] = df_holdings['Current Price'] * df_holdings['quantity']
        df_holdings['PnL (Rp)'] = df_holdings['Value'] - df_holdings['Initial Cost']

        # Hindari pembagian dengan 0
        df_holdings['PnL (%)'] = 0.0
        mask = df_holdings['Initial Cost'] > 0
        df_holdings.loc[mask, 'PnL (%)'] = (df_holdings.loc[mask, 'PnL (Rp)'] / df_holdings.loc[mask, 'Initial Cost']) * 100

        total_value = df_holdings['Value'].sum()
        total_cost = df_holdings['Initial Cost'].sum()
        total_pnl_rp = total_value - total_cost
        total_pnl_pct = (total_pnl_rp / total_cost * 100) if total_cost > 0 else 0.0

        totals = {
            "cost": total_cost,
            "value": total_value,
            "pnl_rp": total_pnl_rp,
            "pnl_pct": total_pnl_pct
        }
        return df_holdings, totals

    # -------------------------
    # I/O Excel
    # -------------------------
    def _persist_to_excel(self):
        """
        Simpan data session_state ke Excel. Overwrite file.
        Dipanggil setelah add/update/remove bila auto_save=True.
        """
        try:
            df = pd.DataFrame(st.session_state.get(self.PORTFOLIO_KEY, []))
            # kalau kosong, hapus file atau buat file kosong? Kita tulis file kosong agar konsisten.
            df.to_excel(self.EXCEL_FILE, index=False)
            # gunakan st.success atau st.experimental_set_query_params bila perlu notif
            st.success(f"💾 Perubahan disimpan ke '{self.EXCEL_FILE}'.")
        except Exception as e:
            st.error(f"❌ Gagal menyimpan ke Excel: {e}")

    def save_to_excel(self, df: pd.DataFrame):
        """Publik: simpan DataFrame manual (dipanggil dari UI jika mau)."""
        if df is None or df.empty:
            st.warning("⚠️ Tidak ada data yang bisa disimpan.")
            return
        try:
            df.to_excel(self.EXCEL_FILE, index=False)
            st.success(f"💾 Data berhasil disimpan di '{self.EXCEL_FILE}'.")
        except Exception as e:
            st.error(f"❌ Gagal menyimpan ke Excel: {e}")

    def load_from_excel(self):
        """
        Load file Excel ke session_state.
        Validasi kolom (symbol, buy_price, quantity).
        Dipanggil hanya saat session_state belum ada (dalam __init__).
        """
        if not os.path.exists(self.EXCEL_FILE):
            # file belum ada → tidak masalah, tunggu saat user tambah data
            return

        try:
            if os.path.getsize(self.EXCEL_FILE) == 0:
                return  # file kosong
            df = pd.read_excel(self.EXCEL_FILE)
            required_cols = {"symbol", "buy_price", "quantity"}
            if not required_cols.issubset(set(df.columns.str.lower())):
                # kolom bisa case-insensitive; normalisasi kolom jika perlu
                cols_lower = {c.lower(): c for c in df.columns}
                if not required_cols.issubset(set(cols_lower.keys())):
                    st.error("❌ Struktur file Excel tidak sesuai. Kolom yang dibutuhkan: symbol, buy_price, quantity")
                    return
                # rebuild DataFrame dengan kolom yang benar jika kolom ada tapi beda case
                df = df.rename(columns={cols_lower[k]: k for k in required_cols if k in cols_lower})
            # Pastikan tipe
            df['symbol'] = df['symbol'].astype(str).str.upper()
            df['buy_price'] = pd.to_numeric(df['buy_price'], errors='coerce').fillna(0.0)
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)

            st.session_state[self.PORTFOLIO_KEY] = df.to_dict('records')
            st.toast("📂 Data portofolio berhasil dimuat dari Excel.")
        except Exception as e:
            st.toast(f"❌ Gagal membaca file Excel: {e}")
