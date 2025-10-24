import streamlit as st
import streamlit.components.v1 as components 
import pandas as pd
import time
import numpy as np
import plotly.graph_objects as go
from typing import List, Tuple, Optional 

# --- Impor Standar ---
from data.data_manager import DataManager
from indicators.moving_average import MovingAverage
from indicators.rsi import RSI
from indicators.macd import MACD
from indicators.bollinger_bands import BollingerBands
from indicators.stochastic import Stochastic
from patterns.reversal_patterns import ReversalPatterns
from analysis.signal_generator import SignalGenerator
from analysis.backtester import Backtester
from machine_learning.predictor import MLPredictor
from visualization.plotter import PlotlyPlotter
from analysis.analyzer import fetch_and_analyze_data
from constants import * 
from portfolio_tracker import PortfolioTracker
from watchlist_tracker import WatchlistTracker

# ==========================================================
# KONFIGURASI STREAMLIT
# ==========================================================
st.set_page_config(
    page_title="Pro Stock Analyzer", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Judul Utama (Style Minimalis & Profesional)
st.markdown(
    """
    <style>
        .stButton>button {border: 2px solid #00FFFF; color: #00FFFF;}
        .stAlert {font-size: 1.1em;}
        h1, h2, h3 {font-family: 'Segoe UI', sans-serif;}
        /* CSS untuk membuat metric P/L berwarna */
        [data-testid="stMetricDelta"] div { color: inherit !important; }
        [data-testid="stMetricDelta"] svg { fill: currentColor !important; }

        /* ========================================================== */
        /* UPGRADE V3.0: Tombol Navigasi Premium di Sidebar */
        /* ========================================================== */
        
        /* Target link navigasi di sidebar */
        [data-testid="stSidebarNav"] ul > li > a {
            padding: 10px 16px;
            margin-bottom: 8px; /* Memberi jarak antar tombol */
            border-radius: 8px; /* Sudut membulat */
            border: 1px solid rgba(255, 255, 255, 0.1); /* Garis batas tipis */
            color: #FAFAFA; /* Teks putih cerah */
            transition: all 0.2s ease-in-out; /* Animasi halus */
        }
        
        /* Saat cursor di atas (hover) */
        [data-testid="stSidebarNav"] ul > li > a:hover {
            background-color: rgba(0, 255, 255, 0.1); /* Efek 'glow' cyan */
            border-color: #00FFFF; /* Garis batas cyan */
            color: #00FFFF; /* Teks cyan */
            text-decoration: none;
        }
        
        /* Untuk halaman yang sedang AKTIF */
        [data-testid="stSidebarNav"] ul > li > a[aria-current="page"] {
            background-color: #00FFFF; /* Latar belakang cyan solid */
            color: #1E1E1E; /* Teks gelap agar kontras */
            font-weight: 600;
            border-color: #00FFFF;
        }
        /* ========================================================== */

    </style>
    # 📈 Pro Stock Analyzer: Dashboard Teknikal Interaktif
    """, unsafe_allow_html=True
)

# ==========================================================
# UPGRADE V2.1.1: Fungsi Helper untuk Ticker
# ==========================================================
def _normalize_ticker(ticker: str) -> str:
    """Memastikan ticker dalam format uppercase dan diakhiri .JK"""
    ticker = ticker.upper().strip()
    if ticker and not ticker.endswith(".JK"):
        ticker += ".JK"
    return ticker

# ==========================================================
# FUNGSI UTAMA ANALISIS
# ==========================================================

def run_analysis(
    ticker: str, 
    period: str, 
    interval: str, 
    auto_update_status: bool,
    current_price_dict: dict, 
    watchlist: list, 
    pt: PortfolioTracker, 
    wt: WatchlistTracker 
):

    # --- VALIDASI INPUT ---
    # (Validasi dasar, normalisasi sudah di sidebar)
    if len(ticker) < 6: # BBCA.JK = 7
        st.error("⚠️ Simbol Ticker tidak valid. Mohon masukkan Simbol Saham yang benar (misalnya: BBCA, GOTO, TLKM).")
        return

    analyzed_data = fetch_and_analyze_data(ticker, period, interval)
    
    if analyzed_data is None: return
    if analyzed_data.empty or len(analyzed_data) < 20: 
        st.warning("Data terlalu sedikit setelah perhitungan indikator. Coba periode yang lebih panjang (Minimal 20 hari/periode).")
        return

    # Inisialisasi Kelas
    signal_gen = SignalGenerator()
    plotter = PlotlyPlotter()
    backtester = Backtester()
    predictor = MLPredictor()
    
    # 3. Hasilkan Sinyal
    action_signals, trend_signals, last_data = signal_gen.generate(analyzed_data, ticker, interval)

    # ==========================================================
    # 4. TAMPILAN DASHBOARD
    # ==========================================================
    
    st.markdown("---")
    st.markdown("## Ringkasan Tren dan Sinyal Terbaru")

    with st.expander("🤔 Apa arti kartu-kartu di bawah ini?"):
        st.markdown(
            """
            Kartu-kartu ini adalah ringkasan cepat dari kondisi pasar **saat ini** (data terakhir):

            - **Harga Penutup:** Harga terakhir yang tercatat.
            - **RSI Terkini:** Mengukur apakah saham sudah *jenuh beli* (**Overbought** > 70) atau *jenuh jual* (**Oversold** < 30).
            - **MACD vs Signal:** Menunjukkan momentum jangka pendek. "Cross Up" adalah sinyal Beli, "Cross Down" adalah sinyal Jual.
            - **Tren MA Kuat:** Menunjukkan tren jangka panjang. "Kuat Naik" (Golden Cross) adalah pertanda baik, "Kuat Turun" (Death Cross) adalah pertanda buruk.
            - **Prediksi ML:** Rekomendasi Beli/Jual dari model Machine Learning (Akurasi menunjukkan seberapa sering model ini benar secara historis).
            """
        )

    # --- UPGRADE V2.1: 3 Kartu Utama (Mobile-Friendly) ---
    col1, col2, col3 = st.columns(3)
    prev_data = analyzed_data.iloc[-2]

    # CARD 1: HARGA PENUTUP
    with col1:
        with st.container(border=True):
            st.metric(
                label=f"Harga Penutup", 
                value=f"Rp {last_data['Close']:,.0f}", 
                delta=f"{last_data['Close'] / prev_data['Close'] * 100 - 100:.2f}%"
            )

    # CARD 2: RSI
    with col2:
        with st.container(border=True):
            rsi_delta = "Overbought" if last_data['RSI'] > RSI_OVERBOUGHT else "Oversold" if last_data['RSI'] < RSI_OVERSOLD else "Netral"
            rsi_delta_color = "inverse" if last_data['RSI'] > RSI_OVERBOUGHT or last_data['RSI'] < RSI_OVERSOLD else "off"
            st.metric(
                label="RSI Terkini", 
                value=f"{last_data['RSI']:.2f}", 
                delta=rsi_delta, 
                delta_color=rsi_delta_color
            )

    # CARD 3: MACD
    with col3:
        with st.container(border=True):
            current_macd_status = "BUY" if last_data['MACD'] > last_data['MACD_Signal'] else "SELL"
            is_cross_up = (last_data['MACD'] > last_data['MACD_Signal']) and (prev_data['MACD'] < prev_data['MACD_Signal'])
            is_cross_down = (last_data['MACD'] < last_data['MACD_Signal']) and (prev_data['MACD'] > prev_data['MACD_Signal'])
            if is_cross_up:
                cross_delta = "Cross Up ⬆️"
                cross_delta_color = "normal"
            elif is_cross_down:
                cross_delta = "Cross Down ⬇️"
                cross_delta_color = "inverse"
            else:
                cross_delta = "Sideways ➡️"
                cross_delta_color = "off"
            st.metric(label="MACD vs Signal", value=current_macd_status, delta=cross_delta, delta_color=cross_delta_color)

    # --- Kartu Tambahan (MA & ML) disembunyikan di expander ---
    with st.expander("Info Tambahan (Tren Jangka Panjang & Prediksi ML)"):
        col4, col5 = st.columns(2)
        # CARD 4: TREN MA KUAT
        with col4:
            with st.container(border=True):
                trend = "Bullish" if last_data['MA_M'] > last_data['MA_L'] else "Bearish" 
                trend_delta = "Kuat Naik ✨" if trend == "Bullish" else "Kuat Turun 💀"
                trend_delta_color = "normal" if trend == "Bullish" else "inverse"
                st.metric(label="Tren MA Kuat", value=trend, delta=trend_delta, delta_color=trend_delta_color)

        # CARD 5: PREDIKSI ML
        with col5:
            with st.container(border=True):
                accuracy, ml_pred = predictor.predict(analyzed_data) 
                pred_delta = f"Rekomendasi {ml_pred}"
                pred_delta_color = "normal" if ml_pred == "BUY" else "inverse" if ml_pred == "SELL" else "off"
                st.metric(label=f"Prediksi ML (Acc: {accuracy*100:.1f}%)", value=ml_pred, delta=pred_delta, delta_color=pred_delta_color)


    # --- UPGRADE V2.1: MTA (Mobile-Friendly Cards) ---
    st.markdown("### 🕒 Ringkasan Analisis Multi-Timeframe (MTA)")
    mta_timeframes = {
        "15 Menit": ("1mo", "15m"), "1 Jam": ("3mo", "1h"),
        "1 Hari": ("1y", "1d"), "1 Minggu": ("max", "1wk")
    }
    mta_results = []
    
    for tf_label, (tf_period, tf_interval) in mta_timeframes.items():
        mta_data = fetch_and_analyze_data(ticker, tf_period, tf_interval)
        if mta_data is None or len(mta_data) < 2:
            mta_results.append({"Timeframe": tf_label, "Status RSI": "N/A", "Status MACD": "N/A"})
            continue
        last, prev = mta_data.iloc[-1], mta_data.iloc[-2]
        if last['RSI'] > RSI_OVERBOUGHT: rsi_status = f"🔴 Overbought ({last['RSI']:.1f})"
        elif last['RSI'] < RSI_OVERSOLD: rsi_status = f"🟢 Oversold ({last['RSI']:.1f})"
        else: rsi_status = f"🟡 Netral ({last['RSI']:.1f})"
        
        if (last['MACD'] > last['MACD_Signal']) and (prev['MACD'] < prev['MACD_Signal']): macd_status = "🟢 BUY (Cross Up)"
        elif (last['MACD'] < last['MACD_Signal']) and (prev['MACD'] > prev['MACD_Signal']): macd_status = "🔴 SELL (Cross Down)"
        elif last['MACD'] > last['MACD_Signal']: macd_status = "🟢 BUY (Tren Naik)"
        else: macd_status = "🔴 SELL (Tren Turun)"
        
        mta_results.append({"Timeframe": tf_label, "Status RSI": rsi_status, "Status MACD": macd_status})

    for row in mta_results:
        with st.container(border=True):
            col_tf, col_rsi, col_macd = st.columns([1, 1, 1])
            col_tf.markdown(f"**{row['Timeframe']}**")
            col_rsi.markdown(f"**RSI:** {row['Status RSI']}")
            col_macd.markdown(f"**MACD:** {row['Status MACD']}")
            
    with st.expander("🤔 Apa itu Analisis Multi-Timeframe (MTA)?"):
        st.markdown(
            """
            MTA adalah teknik profesional untuk mengkonfirmasi sinyal. Sinyal beli terkuat 
            terjadi ketika semua timeframe (jangka pendek, menengah, dan panjang) 
            memberikan sinyal yang sama (misalnya: semua 'BUY').
            """
        )

    # --- Grafik Interaktif (TABS) ---
    st.markdown("---")
    
    tab_harga, tab_indikator, tab_portfolio, tab_watchlist = st.tabs([
        "📊 Grafik Utama (Harga & Volume)", 
        "📈 Indikator Momentum (RSI, MACD)",
        "💼 Portofolio Saya",
        "👀 Watchlist Saya"
    ])
    
    with tab_harga:
        fig_price = plotter.plot_price_chart(analyzed_data, ticker)
        st.plotly_chart(fig_price, use_container_width=True, key=f"price_{str(time.time())}")
    
    with tab_indikator:
        fig_indicators = plotter.plot_indicators_chart(analyzed_data)
        st.plotly_chart(fig_indicators, use_container_width=True, key=f"indicators_{str(time.time())}")

    # --- UPGRADE V2.1: Portofolio (Mobile-Friendly Cards) ---
    with tab_portfolio:
        st.subheader("Ringkasan Portofolio Saya")
        holdings = pt.get_holdings()
        if not holdings:
            st.info("Portofolio Anda masih kosong. Silakan tambah saham pada menu di sidebar (kiri).")
        else:
            df_portfolio, totals = pt.calculate_portfolio_metrics(holdings, current_price_dict)
            
            # Tampilkan Total (Ringkasan)
            col_metrics, col_pie = st.columns([1, 2])
            with col_metrics:
                st.metric("Total Biaya Beli", f"Rp {totals['cost']:,.0f}")
                total_pnl_color = "normal" if totals['pnl_rp'] > 0 else "inverse" if totals['pnl_rp'] < 0 else "off"
                st.metric("Total Nilai Kini", f"Rp {totals['value']:,.0f}", 
                          f"Rp {totals['pnl_rp']:,.0f} ({totals['pnl_pct']:,.2f}%)",
                          delta_color=total_pnl_color)
            with col_pie:
                pie_fig = go.Figure(data=[go.Pie(
                    labels=df_portfolio['symbol'], values=df_portfolio['Value'],
                    textinfo='label+percent', pull=[0.05] * len(df_portfolio), hole=.3
                )])
                pie_fig.update_layout(title_text="Alokasi Aset Berdasarkan Nilai Saat Ini",
                                      template="plotly_dark", margin=dict(t=50, b=0, l=0, r=0),
                                      legend=dict(orientation="h", yanchor="bottom", y=-0.2))
                st.plotly_chart(pie_fig, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Detail Saham (Mobile-Friendly)")

            # Tampilan 'Result Card' (Mobile-Friendly)
            for index, row in df_portfolio.iterrows():
                with st.container(border=True):
                    st.subheader(f"{row['symbol']}")
                    
                    pnl_color = "normal" if row['PnL (Rp)'] > 0 else "inverse" if row['PnL (Rp)'] < 0 else "off"
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Nilai Kini (Value)", f"Rp {row['Value']:,.0f}")
                    col2.metric("Profit/Loss (Rp)", f"Rp {row['PnL (Rp)']:,.0f}", 
                                f"{row['PnL (%)']:.2f}%", delta_color=pnl_color)

                    with st.expander("Tampilkan Detail Transaksi"):
                        c1, c2, c3 = st.columns(3)
                        # UPGRADE V2.1.1: Tampilkan dalam Lot
                        c1.metric("Jumlah", f"{(row['quantity'] / 100):.0f} Lot")
                        c2.metric("Harga Beli Rata-Rata", f"Rp {row['buy_price']:,.0f}")
                        c3.metric("Harga Saat Ini", f"Rp {row['Current Price']:,.0f}")
                        st.write(f"**Total Biaya Beli (Initial Cost):** Rp {row['Initial Cost']:,.0f}")

    # --- UPGRADE V2.1: Watchlist (Mobile-Friendly Cards) ---
    with tab_watchlist:
        st.subheader("Watchlist Saya (Mini-Dashboard)")
        if not watchlist:
            st.info("Watchlist Anda masih kosong. Silakan tambah saham pada menu di sidebar (kiri).")
        else:
            st.info(f"Memindai {len(watchlist)} saham di watchlist Anda menggunakan periode data yang sama...")
            results_list = []
            progress_bar = st.progress(0, text="Memulai pemindaian Watchlist...")
            
            for i, wl_ticker in enumerate(watchlist):
                progress_bar.progress((i + 1) / len(watchlist), text=f"Menganalisis: {wl_ticker}")
                data = fetch_and_analyze_data(wl_ticker, period, interval)
                
                # PERBAIKAN BUG V2.1 (Sudah ada)
                if data is None or len(data) < 2:
                    results_list.append({"Saham": wl_ticker, "Harga Terkini": "N/A", "Perubahan %": "N/A", 
                                         "Status RSI": "N/A", "Status MACD": "Data Error", "Perubahan % (raw)": 0})
                    continue
                    
                last, prev = data.iloc[-1], data.iloc[-2]
                price = last['Close']
                change_pct = (last['Close'] / prev['Close'] * 100) - 100
                if last['RSI'] > RSI_OVERBOUGHT: rsi_status = f"🔴 Overbought ({last['RSI']:.1f})"
                elif last['RSI'] < RSI_OVERSOLD: rsi_status = f"🟢 Oversold ({last['RSI']:.1f})"
                else: rsi_status = f"🟡 Netral ({last['RSI']:.1f})"
                
                if (last['MACD'] > last['MACD_Signal']) and (prev['MACD'] < prev['MACD_Signal']): macd_status = "🟢 BUY (Cross Up)"
                elif (last['MACD'] < last['MACD_Signal']) and (prev['MACD'] > prev['MACD_Signal']): macd_status = "🔴 SELL (Cross Down)"
                elif last['MACD'] > last['MACD_Signal']: macd_status = "🟢 BUY (Tren Naik)"
                else: macd_status = "🔴 SELL (Tren Turun)"
                
                results_list.append({"Saham": wl_ticker, "Harga Terkini": f"Rp {price:,.0f}", 
                                     "Perubahan %": f"{change_pct:.2f}%", "Status RSI": rsi_status, 
                                     "Status MACD": macd_status, "Perubahan % (raw)": change_pct})

            progress_bar.empty()
            df_watchlist = pd.DataFrame(results_list)

            # Tampilan 'Result Card' (Mobile-Friendly)
            for index, row in df_watchlist.iterrows():
                with st.container(border=True):
                    st.subheader(f"{row['Saham']}")
                    delta_color = "normal" if row['Perubahan % (raw)'] > 0 else "inverse" if row['Perubahan % (raw)'] < 0 else "off"
                    st.metric("Harga Terkini", row["Harga Terkini"], row["Perubahan %"], delta_color=delta_color)
                    col1, col2 = st.columns(2)
                    col1.markdown(f"**RSI:** {row['Status RSI']}")
                    col2.markdown(f"**MACD:** {row['Status MACD']}")

    # --- Panel Sinyal & Backtesting ---
    st.markdown("---")
    col_signal, col_backtest = st.columns([2, 1])
    with col_signal:
        col_action, col_trend = st.columns(2)
        with col_action:
            st.subheader("🟢 Sinyal Aksi 🔴")
            if action_signals:
                for signal in action_signals:
                    st.markdown(f"**{signal}**")
            else:
                st.info("Tidak ada sinyal Aksi (Beli/Jual) kuat terdeteksi.")
        with col_trend:
            st.subheader("📊 Konteks Tren 🌊")
            if trend_signals:
                for signal in trend_signals:
                    st.markdown(f"**{signal}**")
            else:
                st.info("Tren terlihat Netral/Sideways.")
        st.markdown("---")
        with st.expander("🤔 Bingung? Klik Saya untuk Penjelasan Sinyal"):
            st.markdown(
                """
                Panel di atas dibagi menjadi dua:
                **1. Sinyal Aksi (Beli/Jual)** - Cepat & Prediktif (RSI, MACD, Pola)
                **2. Konteks Tren (Gambaran Besar)** - Lambat & Konfirmatif (MA)
                **Konflik Sinyal?** "MACD Cross Down" (JUAL) + "MA Golden Cross" (NAIK KUAT)
                **Artinya:** "Tren jangka panjang masih naik, TAPI jangka pendek sedang koreksi. Harap Waspada!"
                """
            )
            
    with col_backtest:
        st.subheader("Hasil Backtesting")
        strategy_options = {
            "MA_CROSS": "Strategi MA Cross", "MACD_TREND": "Strategi Tren MACD",
            "RSI_TREND": "Strategi Tren RSI (> 50)", "RSI_OVER": "Strategi RSI Overbought/Oversold"
        }
        selected_strategy_key = st.selectbox("Pilih Strategi Backtest:",
            options=list(strategy_options.keys()), format_func=lambda x: strategy_options[x],
            key="select_backtest_strategy",
            help="Pilih strategi teknikal yang ingin Anda uji simulasikan kinerjanya di masa lalu."
        )
        metrics_dict = backtester.run_test(analyzed_data, selected_strategy_key) 
        strat_return = metrics_dict.get('total_return_strategy', 0.0)
        stock_return = metrics_dict.get('total_return_stock', 0.0)
        win_rate = metrics_dict.get('win_rate', 0.0)
        profit_factor = metrics_dict.get('profit_factor', 0.0)
        max_drawdown = metrics_dict.get('max_drawdown', 0.0)
        st.metric(label="Pengembalian Strategi", value=f"{strat_return * 100:.2f}%",
            delta=f"{(strat_return - stock_return) * 100:.2f}% vs Saham",
            help="Total keuntungan/kerugian dari strategi ini, dibandingkan dengan hanya membeli dan menahan saham (Beli & Tahan)."
        )
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.metric(label="Win Rate", value=f"{win_rate * 100:.2f}%", help="Persentase dari total transaksi yang ditutup dengan keuntungan.")
            st.metric(label="Profit Factor", value=f"{profit_factor:.2f}" if np.isfinite(profit_factor) else "∞", help="Total untung dibagi total rugi. (Nilai > 1 bagus, < 1 buruk).")
        with col_b2:
            st.metric(label="Max Drawdown", value=f"{max_drawdown * 100:.2f}%", delta_color="inverse", help="Kerugian maksimum dari puncak ke lembah. (Semakin kecil/mendekati 0% semakin baik).")
            st.metric(label="Pengembalian Saham (Beli & Tahan)", value=f"{stock_return * 100:.2f}%", help="Hasil jika Anda hanya membeli di awal dan menjualnya di akhir.")

# --- AKHIR DARI FUNGSI 'run_analysis' ---


# ==========================================================
# 5. SIDEBAR (Konten di-upgrade untuk V2.1.1)
# ==========================================================
period_interval_map = {
    "1 Hari": ("2d", "1m"), "1 Minggu": ("1mo", "15m"), 
    "1 Bulan": ("3mo", "1h"), "1 Tahun": ("1y", "1d"), "Maksimal": ("max", "1wk")
}

with st.sidebar:
    st.header("⚙️ Pengaturan Analisis Saham")
    st.subheader("Data Input")
    
    # UPGRADE V2.1.1: Ambil input mentah
    selected_ticker_input = st.text_input("Simbol Saham (cth: BBCA)", TICKER_DEFAULT)
    
    selected_period_label = st.selectbox("Periode Data", options=list(period_interval_map.keys()), index=3)
    selected_period, selected_interval = period_interval_map[selected_period_label]
    st.info(f"Interval otomatis diatur ke: **{selected_interval}**")
    st.markdown("---")
    
    st.subheader("👀 Watchlist Saya")
    wt = WatchlistTracker()
    watchlist_tickers = wt.get_watchlist()
    with st.form("tambah_watchlist"):
        # UPGRADE V2.1.1: Ambil input mentah
        wl_symbol_input = st.text_input("Simbol Saham", key="wl_add_sym")
        if st.form_submit_button("Tambah ke Watchlist"):
            wl_symbol = _normalize_ticker(wl_symbol_input) # Normalisasi di sini
            wt.add_to_watchlist(wl_symbol)
    if watchlist_tickers:
        selected_wl_ticker = st.selectbox("Pilih Saham untuk Dihapus", options=watchlist_tickers)
        if st.button("Hapus dari Watchlist", key="wl_remove_btn"):
            wt.remove_from_watchlist(selected_wl_ticker)
    st.markdown("---")

    st.subheader("💼 Portofolio Tracker")
    pt = PortfolioTracker()
    with st.form("tambah_portofolio"):
        st.write("Tambah Saham Baru")
        # UPGRADE V2.1.1: Ambil input mentah
        port_symbol_input = st.text_input("Simbol", key="p_sym")
        port_price = st.number_input("Harga Beli", min_value=1.0, step=1.0, key="p_price")
        # UPGRADE V2.1.1: Ubah label ke 'Lot'
        port_qty_lots = st.number_input("Jumlah Lot", min_value=1, step=1, key="p_qty", format="%i")
        
        submitted = st.form_submit_button("Tambah Saham")
        if submitted and port_symbol_input and port_price and port_qty_lots:
            # Normalisasi ticker dan konversi Lot ke Lembar
            port_symbol = _normalize_ticker(port_symbol_input)
            port_qty_lembar = port_qty_lots * 100
            pt.add_holding(port_symbol, port_price, port_qty_lembar)
            st.rerun() 

    holdings = pt.get_holdings()
    if holdings:
        st.markdown("---")
        st.write("Edit/Hapus Saham")
        # UPGRADE V2.1.1: Tampilkan dalam Lot
        holding_options = [f"{i}: {h['symbol']} ({(h['quantity'] / 100):.0f} Lot @ Rp{h['buy_price']:,.0f})" for i, h in enumerate(holdings)]
        
        default_index = 0
        selected_index_str = st.selectbox("Pilih Saham", options=holding_options, index=default_index, key="select_edit_delete")
        if holding_options:
            selected_index = int(selected_index_str.split(':')[0])
            selected_holding = holdings[selected_index]
            col_edit_form1, col_edit_form2 = st.columns(2)
            with col_edit_form2:
                if st.button("Hapus", key="delete_holding"):
                    pt.remove_holding(selected_index)
                    st.toast(f"Berhasil menghapus {selected_holding['symbol']}.")
                    st.rerun() 
            with col_edit_form1:
                with st.form("edit_portofolio"):
                    st.write(f"Edit {selected_holding['symbol']}")
                    # UPGRADE V2.1.1: Ambil input mentah
                    edit_symbol_input = st.text_input("Simbol Baru", value=selected_holding['symbol'].replace(".JK", ""), key="e_sym")
                    edit_price = st.number_input("Harga Beli Baru", min_value=1.0, step=1.0, value=selected_holding['buy_price'], key="e_price")
                    # UPGRADE V2.1.1: Tampilkan dan ambil input dalam Lot
                    edit_qty_lots = st.number_input("Jumlah Lot Baru", min_value=1, step=1, value=int(selected_holding['quantity'] / 100), key="e_qty", format="%i")
                    
                    edit_submitted = st.form_submit_button("Simpan Perubahan")
                    if edit_submitted:
                        # Normalisasi ticker dan konversi Lot ke Lembar
                        edit_symbol = _normalize_ticker(edit_symbol_input)
                        edit_qty_lembar = edit_qty_lots * 100
                        pt.update_holding(selected_index, edit_symbol, edit_price, edit_qty_lembar)
                        st.success(f"Berhasil memperbarui {edit_symbol}.")
                        st.rerun() 
        else:
            pass

    @st.cache_data(ttl=300)
    def fetch_current_prices(tickers):
        data_manager_sidebar = DataManager(None, None, None)
        price_dict = {}
        for t in tickers:
            try:
                # Pastikan ticker yang dikirim ke fetch sudah ternormalisasi
                normalized_t = _normalize_ticker(t)
                temp_data = data_manager_sidebar.fetch_data(normalized_t, "1d", "1d") 
                if temp_data is not None and 'Close' in temp_data.columns and not temp_data.empty:
                    price_dict[t] = temp_data.iloc[-1]['Close']
                else: price_dict[t] = 0.0
            except Exception: price_dict[t] = 0.0
        return price_dict

    tickers_in_portfolio = list(set(h['symbol'] for h in holdings))
    current_price_dict = {}
    if tickers_in_portfolio:
        current_price_dict = fetch_current_prices(tickers_in_portfolio)
    
    st.markdown("---")
    st.subheader("Pembaruan & Notifikasi")
    update_interval = 60
    auto_update = True 
    st.info(f"Pembaruan otomatis via browser: {update_interval} detik.")
    if auto_update:
        components.html(f"""<meta http-equiv="refresh" content="{update_interval}">""", height=0, width=0)

    st.sidebar.markdown("---")
    st.sidebar.caption("© 2025 Dibuat oleh Hendrawan Lotanto.")
    # ==========================================================
    # UPGRADE V3.0: Update Versi
    # ==========================================================
    st.sidebar.caption("Versi 3.0.0 (Database Permanen)")


# ==========================================================
# 6. RUN APLIKASI UTAMA
# ==========================================================

# UPGRADE V2.1.1: Normalisasi ticker input utama sebelum di-pass
selected_ticker = _normalize_ticker(selected_ticker_input)

if selected_ticker:
    start_time = time.time() 
    st.info(f"⏳ Menganalisis {selected_ticker}...")
    
    run_analysis(
        selected_ticker, selected_period, selected_interval, None,
        current_price_dict, wt.get_watchlist(), pt, wt 
    )
    
    end_time = time.time()
    st.sidebar.markdown(f"---")
    st.sidebar.success(f"Analisis Selesai dalam **{end_time - start_time:.2f} detik**.")

# Tambahkan else untuk Tampilan Awal
else:
    st.info("Silakan masukkan Simbol Saham di sidebar (kiri) untuk memulai analisis.")

