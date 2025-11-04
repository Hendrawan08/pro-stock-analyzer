# pages/7_📈_Simulasi_Trading.py

from utils.auth import check_password
import os
try:
    import streamlit as st
except Exception:
    st = None
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
from typing import List
import sys, os

# ======== IMPORT DARI ROOT FOLDER ========
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from trading_log_tracker import TradingLogTracker
    from data.data_manager import fetch_data
    from visualization.plotter import PlotlyPlotter
except ImportError:
    st.error("Gagal mengimpor modul. Pastikan menjalankan Streamlit dari folder root.")
    st.stop()

# ==========================================================
# PASSWORD ANDA DI SINI
# ==========================================================

if not check_password("📈 Simulasi Trading"):
    st.stop()  # Hentikan eksekusi sisa skrip jika password salah

# --- Jika lolos, lanjutkan ke konten admin ---
st.success("Password Diterima. Selamat Datang, Kreator!")

# ==========================================================

# ======== KONFIGURASI HALAMAN ========
st.set_page_config(page_title="Simulasi Trading", layout="wide")
st.markdown("# 📈 Simulasi Trading")
st.warning("Simulasi ini hanya aktif saat halaman terbuka. TP/SL tidak otomatis saat ditutup.")
st.markdown("---")

# ======== STYLING ========
st.markdown("""
<style>
div.stButton button {
    border-radius: 10px;
    height: 42px;
    font-weight: 600;
    background-color: #4A90E2 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ======== HELPER ========
def _normalize_ticker(ticker: str) -> str:
    t = ticker.strip().upper()
    if not t.endswith(".JK"):
        t += ".JK"
    return t

@st.cache_data(ttl=60)
def fetch_current_prices(tickers: List[str]) -> dict:
    """Ambil harga terkini (interval 1m)."""
    if not tickers:
        return {}
    normalized = [_normalize_ticker(t) for t in tickers]
    try:
        data = yf.download(normalized, period="1d", interval="1m", progress=False)
        prices = {}
        if data.empty:
            return {t: 0.0 for t in tickers}
        if len(normalized) == 1:
            last_price = data["Close"].dropna().iloc[-1]
            prices[tickers[0]] = float(last_price)
        else:
            last_prices = data["Close"].dropna().iloc[-1].to_dict()
            for t in tickers:
                prices[t] = float(last_prices.get(_normalize_ticker(t), 0.0))
        return prices
    except Exception as e:
        st.warning(f"Gagal mengambil harga: {e}")
        return {t: 0.0 for t in tickers}

@st.cache_data(ttl=60)
def get_stock_data_for_sim(ticker):
    data = fetch_data(ticker, "1y", "1d")
    price_dict = fetch_current_prices([ticker])
    price = price_dict.get(ticker, 0.0)
    if price == 0.0 and data is not None and not data.empty:
        price = data.iloc[-1]["Close"]
    return data, price

# ======== INIT TRACKER & PLOTTER ========
tracker = TradingLogTracker()
plotter = PlotlyPlotter()

# ======== CEK POSISI TERBUKA ========
open_positions = tracker.get_open_positions()
if not open_positions.empty:
    tickers_to_check = open_positions["symbol"].unique().tolist()
    current_prices = fetch_current_prices(tickers_to_check)
    for _, trade in open_positions.iterrows():
        symbol = trade["symbol"]
        trade_id = trade["id"]
        current_price = current_prices.get(symbol, 0.0)
        if current_price == 0.0:
            continue
        # Lewati posisi yang baru dibuka <1 menit
        timestamp_open = pd.to_datetime(trade["timestamp_open"], errors="coerce")
        if (datetime.now() - timestamp_open).total_seconds() < 60:
            continue
        if current_price >= trade["tp_price"]:
            success, pnl = tracker.close_trade(trade_id, trade["tp_price"], "PROFIT")
            if success: st.toast(f"🎉 TP {symbol} di Rp {trade['tp_price']:,.0f}. Profit Rp {pnl:,.0f}")
        elif current_price <= trade["sl_price"]:
            success, pnl = tracker.close_trade(trade_id, trade["sl_price"], "LOSS")
            if success: st.toast(f"💔 SL {symbol} di Rp {trade['sl_price']:,.0f}. Loss Rp {pnl:,.0f}")

# ======== BAGIAN 1: BUKA POSISI ========
st.header("Buka Posisi Trading Baru")

if "ticker_input" not in st.session_state:
    st.session_state.ticker_input = ""
if "sim_ticker" not in st.session_state:
    st.session_state.sim_ticker = ""

def on_search_click():
    st.session_state.sim_ticker = _normalize_ticker(st.session_state.ticker_input)

col_search, col_btn = st.columns([4, 1])
with col_search:
    st.text_input("Cari Saham", key="ticker_input", placeholder="cth: BBCA")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("🔍 Cari", on_click=on_search_click, use_container_width=True)

if st.session_state.sim_ticker:
    data, current_price = get_stock_data_for_sim(st.session_state.sim_ticker)
    if data is None:
        st.error(f"Data tidak ditemukan untuk {st.session_state.sim_ticker}")
    else:
        st.metric(f"Harga {st.session_state.sim_ticker}", f"Rp {current_price:,.0f}")
        fig = plotter.plot_price_chart(data, st.session_state.sim_ticker)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        st.subheader("Atur Rencana Trading")

        with st.form("buy_form"):
            default_tp = current_price * 1.1
            default_sl = current_price * 0.95
            c1, c2 = st.columns(2)
            with c1:
                entry = st.number_input("Harga Beli", value=current_price, step=50.0)
                lots = st.number_input("Jumlah Lot", min_value=1, value=10, step=1)
            with c2:
                tp = st.number_input("Take Profit", value=default_tp, step=50.0, min_value=entry)
                sl = st.number_input("Stop Loss", value=default_sl, step=50.0, max_value=entry)
            if st.form_submit_button("🚀 Beli (Simulasi)", type="primary"):
                if tp <= entry:
                    st.error("TP harus di atas harga beli.")
                elif sl >= entry:
                    st.error("SL harus di bawah harga beli.")
                else:
                    tracker.add_trade(st.session_state.sim_ticker, entry, lots, tp, sl)
                    st.success(f"✅ Beli {lots} lot {st.session_state.sim_ticker} di Rp {entry:,.0f}")
                    st.toast("Posisi baru ditambahkan!", icon="📊")
                    st.session_state.sim_ticker = ""
                    st.rerun()

st.markdown("---")

# ======== BAGIAN 2: DAFTAR POSISI ========
st.header("📒 Jurnal Trading Anda")
all_trades = tracker.get_all_trades()

if all_trades.empty:
    st.info("Belum ada data trading.")
else:
    df_open = all_trades[all_trades["status"] == "OPEN"].copy()
    df_closed = all_trades[all_trades["status"] != "OPEN"].copy()

    # ==== Posisi Terbuka ====
    st.subheader("Posisi Terbuka")
    if df_open.empty:
        st.info("Tidak ada posisi terbuka.")
    else:
        live = fetch_current_prices(df_open["symbol"].unique().tolist())
        df_open["current_price"] = df_open["symbol"].map(live)
        df_open["unrealized_pnl"] = (df_open["current_price"] - df_open["entry_price"]) * df_open["lots"] * 100
        df_display = df_open[["timestamp_open", "symbol", "entry_price", "current_price", "tp_price", "sl_price", "lots", "unrealized_pnl"]]
        df_display.columns = ["Tgl Beli", "Symbol", "Entry", "Harga Kini", "TP", "SL", "Lot", "Unrealized PnL"]
        df_display["Tgl Beli"] = pd.to_datetime(df_display["Tgl Beli"]).dt.strftime("%Y-%m-%d %H:%M")
        for c in ["Entry", "Harga Kini", "TP", "SL", "Unrealized PnL"]:
            df_display[c] = df_display[c].apply(lambda x: f"Rp {x:,.0f}")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.markdown("### Kelola Posisi Terbuka")
        if "delete_confirm_id" not in st.session_state:
            st.session_state.delete_confirm_id = None

        for _, row in df_open.iterrows():
            trade_id = row["id"]
            symbol = row["symbol"]
            with st.expander(f"⚙️ {symbol} — Entry Rp {row['entry_price']:,.0f}"):
                c1, c2 = st.columns(2)
                with c1:
                    with st.form(f"edit_{trade_id}"):
                        new_tp = st.number_input("Edit TP", value=float(row["tp_price"]), step=50.0, key=f"tp_{trade_id}")
                        new_sl = st.number_input("Edit SL", value=float(row["sl_price"]), step=50.0, key=f"sl_{trade_id}")
                        if st.form_submit_button("💾 Simpan"):
                            tracker.trades_df.loc[tracker.trades_df["id"] == trade_id, ["tp_price", "sl_price"]] = [new_tp, new_sl]
                            tracker.save_trades()
                            st.success("✅ Disimpan.")
                            st.rerun()

                with c2:
                    if st.session_state.delete_confirm_id == trade_id:
                        st.warning(f"Yakin hapus posisi {symbol}?")
                        cxa, cxb = st.columns(2)
                        with cxa:
                            if st.button("✅ Ya", key=f"yes_{trade_id}"):
                                tracker.trades_df = tracker.trades_df[tracker.trades_df["id"] != trade_id]
                                tracker.save_trades()
                                st.session_state.delete_confirm_id = None
                                st.success("🗑️ Dihapus.")
                                st.rerun()
                        with cxb:
                            if st.button("❌ Batal", key=f"no_{trade_id}"):
                                st.session_state.delete_confirm_id = None
                                st.rerun()
                    else:
                        if st.button(f"🗑️ Hapus {symbol}", key=f"del_{trade_id}"):
                            st.session_state.delete_confirm_id = trade_id
                            st.rerun()

    # ==== Riwayat Tertutup ====
    st.subheader("Riwayat Transaksi")
    if df_closed.empty:
        st.info("Belum ada transaksi tertutup.")
    else:
        total_profit = df_closed[df_closed["pnl_rp"] > 0]["pnl_rp"].sum()
        total_loss = df_closed[df_closed["pnl_rp"] < 0]["pnl_rp"].sum()
        win_trades = len(df_closed[df_closed["status"] == "PROFIT"])
        loss_trades = len(df_closed[df_closed["status"] == "LOSS"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Profit", f"Rp {total_profit:,.0f}")
        c2.metric("Total Loss", f"Rp {total_loss:,.0f}")
        c3.metric("Win Rate", f"{(win_trades / (win_trades + loss_trades) * 100):.1f}%" if (win_trades + loss_trades) > 0 else "N/A")

        pie = go.Figure(go.Pie(
            labels=["Profit", "Loss"],
            values=[win_trades, loss_trades],
            marker_colors=["#2ca02c", "#d62728"]
        ))
        pie.update_layout(title_text="Ringkasan Transaksi", margin=dict(t=40, l=10, r=10, b=10))
        st.plotly_chart(pie, use_container_width=True)

        df_closed_display = df_closed[["timestamp_close", "symbol", "status", "entry_price", "exit_price", "lots", "pnl_rp"]]
        df_closed_display.columns = ["Tgl Tutup", "Symbol", "Status", "Entry", "Exit", "Lot", "PnL (Rp)"]
        df_closed_display["Tgl Tutup"] = pd.to_datetime(df_closed_display["Tgl Tutup"]).dt.strftime("%Y-%m-%d %H:%M")
        for c in ["Entry", "Exit", "PnL (Rp)"]:
            df_closed_display[c] = df_closed_display[c].apply(lambda x: f"Rp {x:,.0f}")
        st.dataframe(df_closed_display, use_container_width=True, hide_index=True)
