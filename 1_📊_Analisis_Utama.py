#1_📊_Analisis_Utama.py

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
import numpy as np
import plotly.graph_objects as go
from typing import List, Tuple, Optional
import yfinance as yf

# --- Impor Standar ---
from indicators.moving_average import MovingAverage
from indicators.rsi import RSI
from indicators.macd import MACD
from indicators.bollinger_bands import BollingerBands
from indicators.stochastic import Stochastic
from patterns.reversal_patterns import ReversalPatterns
from analysis.signal_generator import SignalGenerator
from analysis.backtester import Backtester
from machine_learning.predictor import MLPredictor # <-- V11.0 Model Ensemble
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
st.markdown(
    """
    <style>
        .stButton>button {border: 2px solid #00FFFF; color: #00FFFF;}
        .stAlert {font-size: 1.1em;}
        h1, h2, h3 {font-family: 'Segoe UI', sans-serif;}
        [data-testid="stMetricDelta"] div { color: inherit !important; }
        [data-testid="stMetricDelta"] svg { fill: currentColor !important; }
    </style>
    # 📈 Pro Stock Analyzer: Dashboard Teknikal Interaktif
    """, unsafe_allow_html=True
)

# ==========================================================
# FUNGSI HELPER (Tidak berubah)
# ==========================================================
def _normalize_ticker(ticker: str) -> str:
    ticker = ticker.upper().strip()
    if ticker and not ticker.endswith(".JK"):
        ticker += ".JK"
    return ticker

@st.cache_data(ttl=300, show_spinner="Memuat harga terkini...")
def fetch_current_prices(tickers: List[str]) -> dict:
    price_dict = {}
    if not tickers:
        return price_dict
        
    normalized_tickers = [_normalize_ticker(t) for t in tickers]
    try:
        data = yf.download(normalized_tickers, period='2d', interval='1d', progress=False)
        
        # (PERBAIKAN) Logika penanganan data kosong yang lebih aman
        if data.empty:
            return {ticker: 0.0 for ticker in tickers}

        if len(normalized_tickers) == 1:
            # (PERBAIKAN) Logika UnboundLocalError diperbaiki
            # Pastikan data, kolom 'Close', dan isinya tidak kosong sebelum diakses
            if not data.empty and 'Close' in data.columns and not data['Close'].empty:
                last_price = data['Close'].iloc[-1]
            else:
                last_price = 0.0
            price_dict_normalized = {normalized_tickers[0]: last_price}
        
        else:
            # (PERBAIKAN) Logika Multi-ticker yang aman, menghindari IndexError
            close_data = data.get('Close')
            
            # Cek apakah 'Close' ada dan bukan Series kosong (jika yf.download gagal sebagian)
            if close_data is None or close_data.empty or not isinstance(close_data, pd.DataFrame):
                price_dict_normalized = {t: 0.0 for t in normalized_tickers}
            else:
                # 'close_data' adalah DataFrame, ambil baris terakhir sebagai Series
                last_prices_series = close_data.iloc[-1]
                price_dict_normalized = last_prices_series.to_dict()

        # (Logika lama Anda untuk memetakan kembali sudah benar)
        final_price_dict = {}
        for original_ticker in tickers:
            norm_t = _normalize_ticker(original_ticker)
            price = price_dict_normalized.get(norm_t, 0.0)
            final_price_dict[original_ticker] = 0.0 if pd.isna(price) else price
        
        return final_price_dict
        
    except Exception as e:
        # Sekarang ini akan menangkap error yang sesungguhnya dengan lebih jelas
        st.warning(f"Gagal mengambil beberapa harga terkini: {e}")
        return {ticker: 0.0 for ticker in tickers}

# ==========================================================
# FUNGSI UTAMA ANALISIS (V11.1)
# ==========================================================
def run_analysis(
    ticker: str, period: str, interval: str, auto_update_status: bool,
    current_price_dict: dict, watchlist: list, pt: PortfolioTracker, wt: WatchlistTracker
):
    if len(ticker) < 6:
        st.error("⚠️ Simbol Ticker tidak valid (Harus 4 huruf + .JK)")
        return
    
    analyzed_data = fetch_and_analyze_data(ticker, period, interval)
    if analyzed_data is None: return
    if analyzed_data.empty or len(analyzed_data) < 20:
        st.warning("Data terlalu sedikit untuk dianalisis...")
        return

    signal_gen = SignalGenerator()
    plotter = PlotlyPlotter()
    backtester = Backtester()
    predictor = MLPredictor() # <-- V11.0
    
    # --- PERUBAHAN V11.1: Tangkap 'narrative' ---
    action_signals, trend_signals, last_data, narrative = signal_gen.generate(analyzed_data, ticker, interval)
    # -------------------------------------------
    
    if 'Sentiment_Score' not in last_data:
        st.error("Kolom 'Sentiment_Score' tidak ditemukan. Cek `analysis/analyzer.py`.")
        return 

    st.markdown("---")
    st.markdown("## Ringkasan Tren dan Sinyal Terbaru")
    
    # --- PERUBAHAN V11.1: Tampilkan "Story of the Chart" ---
    st.info(f"✍️ **Ringkasan Analis Otomatis:** {narrative}")
    # ----------------------------------------------------
    
    with st.expander("🤔 Apa arti kartu-kartu di bawah ini?"):
        st.markdown(
            """
            Kartu-kartu ini adalah ringkasan cepat dari kondisi pasar **saat ini** (data terakhir). Arahkan kursor ke ikon `(?)` di setiap kartu untuk penjelasan mendetail.
            """
        )
    
    col1, col2, col3, col4 = st.columns(4)
    prev_data = analyzed_data.iloc[-2]

    # --- PERUBAHAN V11.1: Tambahkan Tooltips 'help=...' ---
    with col1:
        with st.container(border=True):
            score = last_data['Sentiment_Score']
            if score >= 70: delta_label, delta_color = "Bullish Kuat 🔥", "normal"
            elif score >= 50: delta_label, delta_color = "Bullish 🟢", "normal"
            elif score > 40: delta_label, delta_color = "Netral 🟡", "off"
            else: delta_label, delta_color = "Bearish 🔴", "inverse"
            st.metric(
                label="Skor Sentimen", 
                value=f"{score:.0f} / 100", 
                delta=delta_label, 
                delta_color=delta_color,
                help="Skor gabungan (0-100) dari Tren Jangka Panjang (MA), Momentum Jangka Menengah (MACD), dan Kondisi Jenuh Jual/Beli (RSI)."
            )
    with col2:
        with st.container(border=True):
            st.metric(
                label=f"Harga Penutup", 
                value=f"Rp {last_data['Close']:,.0f}", 
                delta=f"{last_data['Close'] / prev_data['Close'] * 100 - 100:.2f}%",
                help="Harga penutup terakhir yang tercatat, dengan % perubahan dari hari sebelumnya."
            )
    with col3:
        with st.container(border=True):
            rsi_delta = "Overbought" if last_data['RSI'] > RSI_OVERBOUGHT else "Oversold" if last_data['RSI'] < RSI_OVERSOLD else "Netral"
            rsi_delta_color = "inverse" if last_data['RSI'] > RSI_OVERBOUGHT or last_data['RSI'] < RSI_OVERSOLD else "off"
            st.metric(
                label="RSI Terkini", 
                value=f"{last_data['RSI']:.2f}", 
                delta=rsi_delta, 
                delta_color=rsi_delta_color,
                help="Relative Strength Index (14). Nilai < 30 dianggap 'Oversold' (Jenuh Jual, potensi beli). Nilai > 70 dianggap 'Overbought' (Jenuh Beli, potensi jual)."
            )
    with col4:
        with st.container(border=True):
            current_macd_status = "BUY" if last_data['MACD'] > last_data['MACD_Signal'] else "SELL"
            is_cross_up = (last_data['MACD'] > last_data['MACD_Signal']) and (prev_data['MACD'] < prev_data['MACD_Signal'])
            is_cross_down = (last_data['MACD'] < last_data['MACD_Signal']) and (prev_data['MACD'] > prev_data['MACD_Signal'])
            if is_cross_up: cross_delta, cross_delta_color = "Cross Up ⬆️", "normal"
            elif is_cross_down: cross_delta, cross_delta_color = "Cross Down ⬇️", "inverse"
            else: cross_delta, cross_delta_color = "Sideways ➡️", "off"
            st.metric(
                label="MACD vs Signal", 
                value=current_macd_status, 
                delta=cross_delta, 
                delta_color=cross_delta_color,
                help="Menunjukkan momentum. Jika garis MACD (biru) di atas Garis Sinyal (oranye), momentum adalah 'BUY' (positif). 'Cross Up' adalah sinyal beli kuat."
            )
    # -------------------------------------------------

    with st.expander("Info Tambahan (Tren Jangka Panjang & Prediksi ML)"):
        col5, col6 = st.columns(2) 
        with col5:
            with st.container(border=True):
                trend = "Bullish" if last_data['MA_M'] > last_data['MA_L'] else "Bearish"
                trend_delta = "Kuat Naik ✨" if trend == "Bullish" else "Kuat Turun 💀"
                trend_delta_color = "normal" if trend == "Bullish" else "inverse"
                st.metric(
                    label="Tren MA Kuat", 
                    value=trend, 
                    delta=trend_delta, 
                    delta_color=trend_delta_color,
                    help=f"Membandingkan MA {MA_MEDIUM_WINDOW} (Jangka Menengah) dengan MA {MA_LONG_WINDOW} (Jangka Panjang). Jika MA Menengah > MA Panjang, tren dianggap Bullish kuat."
                )
        with col6:
            with st.container(border=True):
                if len(analyzed_data) < 70:
                    accuracy, ml_pred = 0.0, "Data N/A"
                else:
                    accuracy, ml_pred = predictor.predict(analyzed_data) # <-- V11.0
                pred_delta = f"Rekomendasi {ml_pred}"
                pred_delta_color = "normal" if ml_pred == "BUY" else "inverse" if ml_pred == "SELL" else "off"
                st.metric(
                    label=f"Prediksi ML (Ensemble)", 
                    value=ml_pred, 
                    delta=pred_delta, 
                    delta_color=pred_delta_color,
                    help=f"Prediksi dari Model Ensemble (V11.0) apakah harga akan lebih tinggi dalam 5 hari ke depan. Akurasi pada data tes historis: {accuracy*100:.1f}%"
                )

    st.markdown("### 🕒 Ringkasan Analisis Multi-Timeframe (MTA)")
    mta_timeframes = {"15 Menit": ("1mo", "15m"), "1 Jam": ("3mo", "1h"), "1 Hari": ("1y", "1d"), "1 Minggu": ("max", "1wk")}
    mta_results = []
    for tf_label, (tf_period, tf_interval) in mta_timeframes.items():
        @st.cache_data(ttl=300) 
        def get_mta_data(t, p, i):
            return fetch_and_analyze_data(t, p, i)
        
        mta_data = get_mta_data(ticker, tf_period, tf_interval)
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
            col_tf, col_rsi, col_macd = st.columns([1, 1, 1]); 
            col_tf.markdown(f"**{row['Timeframe']}**"); 
            col_rsi.markdown(f"**RSI:** {row['Status RSI']}"); 
            col_macd.markdown(f"**MACD:** {row['Status MACD']}")
            
    with st.expander("🤔 Apa itu Analisis Multi-Timeframe (MTA)?"):
        st.markdown("MTA adalah teknik profesional untuk mengkonfirmasi sinyal. Sinyal beli terkuat terjadi ketika semua timeframe (jangka pendek, menengah, dan panjang) memberikan sinyal yang sama (misalnya: semua 'BUY').")
        
    st.markdown("---")
    tab_harga, tab_indikator, tab_portfolio, tab_watchlist = st.tabs(["📊 Grafik Utama (Harga & Volume)", "📈 Indikator Momentum (RSI, MACD)", "💼 Portofolio Saya", "👀 Watchlist Saya"])
    
    with tab_harga:
        fig_price = plotter.plot_price_chart(analyzed_data, ticker); 
        st.plotly_chart(fig_price, use_container_width=True, key=f"price_{str(time.time())}")
    with tab_indikator:
        fig_indicators = plotter.plot_indicators_chart(analyzed_data); 
        st.plotly_chart(fig_indicators, use_container_width=True, key=f"indicators_{str(time.time())}")
    
    with tab_portfolio:
        st.subheader("Ringkasan Portofolio Saya")
        holdings = pt.get_holdings()
        if not holdings: 
            st.info("Portofolio Anda masih kosong. Tambahkan saham melalui sidebar.")
        else:
            df_portfolio, totals = pt.calculate_portfolio_metrics(holdings, current_price_dict)
            col_metrics, col_pie = st.columns([1, 2])
            with col_metrics:
                st.metric("Total Biaya Beli", f"Rp {totals['cost']:,.0f}"); 
                total_pnl_color = "normal" if totals['pnl_rp'] > 0 else "inverse" if totals['pnl_rp'] < 0 else "off"; 
                st.metric("Total Nilai Kini", f"Rp {totals['value']:,.0f}", f"Rp {totals['pnl_rp']:,.0f} ({totals['pnl_pct']:,.2f}%)", delta_color=total_pnl_color)
            with col_pie:
                pie_fig = go.Figure(data=[go.Pie(labels=df_portfolio['symbol'], values=df_portfolio['Value'], textinfo='label+percent', pull=[0.05] * len(df_portfolio), hole=.3)]); 
                pie_fig.update_layout(title_text="Alokasi Aset Berdasarkan Nilai Saat Ini", template="plotly_dark", margin=dict(t=50, b=0, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=-0.2)); 
                st.plotly_chart(pie_fig, use_container_width=True)
            st.markdown("---"); st.subheader("Detail Saham (Mobile-Friendly)")
            for index, row in df_portfolio.iterrows():
                with st.container(border=True):
                    st.subheader(f"{row['symbol']}"); 
                    pnl_color = "normal" if row['PnL (Rp)'] > 0 else "inverse" if row['PnL (Rp)'] < 0 else "off"; 
                    col1, col2 = st.columns(2); 
                    col1.metric("Nilai Kini (Value)", f"Rp {row['Value']:,.0f}"); 
                    col2.metric("Profit/Loss (Rp)", f"Rp {row['PnL (Rp)']:,.0f}", f"{row['PnL (%)']:.2f}%", delta_color=pnl_color)
                    with st.expander("Tampilkan Detail Transaksi"):
                        c1, c2, c3 = st.columns(3); 
                        c1.metric("Jumlah", f"{(row['quantity'] / 100):.0f} Lot"); 
                        c2.metric("Harga Beli Rata-Rata", f"Rp {row['buy_price']:,.0f}"); 
                        c3.metric("Harga Saat Ini", f"Rp {row['Current Price']:,.0f}"); 
                        st.write(f"**Total Biaya Beli (Initial Cost):** Rp {row['Initial Cost']:,.0f}")
            col_save_a, col_save_b = st.columns([1, 3]); 
            with col_save_a:
                if st.button("💾 Simpan Portofolio ke Excel"): pt.save_to_excel(df_portfolio)
            with col_save_b: st.info("Snapshot ini akan menimpa file 'portfolio_data.xlsx' Anda.")
            
    with tab_watchlist:
        st.subheader("Watchlist Saya (Mini-Dashboard)")
        if not watchlist: 
            st.info("Watchlist Anda masih kosong. Tambahkan saham melalui sidebar.")
        else:
            st.info(f"Memindai {len(watchlist)} saham (data harian)...")
            results_list = []; 
            progress_bar = st.progress(0, text="Memulai pemindaian Watchlist...")
            for i, wl_ticker in enumerate(watchlist):
                progress_bar.progress((i + 1) / len(watchlist), text=f"Menganalisis: {wl_ticker}"); 
                
                @st.cache_data(ttl=300) 
                def get_wl_data(t):
                    return fetch_and_analyze_data(t, "3mo", "1d")

                data = get_wl_data(wl_ticker)
                if data is None or len(data) < 2: 
                    results_list.append({"Saham": wl_ticker, "Harga Terkini": "N/A", "Perubahan %": "N/A", "Status RSI": "N/A", "Status MACD": "Data Error", "Perubahan % (raw)": 0}); 
                    continue
                last, prev = data.iloc[-1], data.iloc[-2]; 
                price = last['Close']; 
                change_pct = (last['Close'] / prev['Close'] * 100) - 100
                if last['RSI'] > RSI_OVERBOUGHT: rsi_status = f"🔴 Overbought ({last['RSI']:.1f})"
                elif last['RSI'] < RSI_OVERSOLD: rsi_status = f"🟢 Oversold ({last['RSI']:.1f})"
                else: rsi_status = f"🟡 Netral ({last['RSI']:.1f})"
                if (last['MACD'] > last['MACD_Signal']) and (prev['MACD'] < prev['MACD_Signal']): macd_status = "🟢 BUY (Cross Up)"
                elif (last['MACD'] < last['MACD_Signal']) and (prev['MACD'] > prev['MACD_Signal']): macd_status = "🔴 SELL (Cross Down)"
                elif last['MACD'] > last['MACD_Signal']: macd_status = "🟢 BUY (Tren Naik)"
                else: macd_status = "🔴 SELL (Tren Turun)"
                results_list.append({"Saham": wl_ticker, "Harga Terkini": f"Rp {price:,.0f}", "Perubahan %": f"{change_pct:.2f}%", "Status RSI": rsi_status, "Status MACD": macd_status, "Perubahan % (raw)": change_pct})
            
            progress_bar.empty(); 
            df_watchlist = pd.DataFrame(results_list)
            for index, row in df_watchlist.iterrows():
                with st.container(border=True):
                    st.subheader(f"{row['Saham']}"); 
                    delta_color = "normal" if row['Perubahan % (raw)'] > 0 else "inverse" if row['Perubahan % (raw)'] < 0 else "off"; 
                    st.metric("Harga Terkini", row["Harga Terkini"], row["Perubahan %"], delta_color=delta_color); 
                    col1, col2 = st.columns(2); 
                    col1.markdown(f"**RSI:** {row['Status RSI']}"); 
                    col2.markdown(f"**MACD:** {row['Status MACD']}")
            col_w_a, col_w_b = st.columns([1, 3]); 
            with col_w_a:
                if st.button("💾 Simpan Daftar Watchlist ke Excel"): wt.save_to_excel()
            with col_w_b: st.info("Snapshot ini akan menimpa file 'watchlist_data.xlsx' Anda.")
    
    st.markdown("---") 
    col_signal, col_backtest = st.columns([2, 1])
    with col_signal:
        col_action, col_trend = st.columns(2); 
        with col_action: 
            st.subheader("🟢 Sinyal Aksi 🔴"); 
            if action_signals:
                for s in action_signals: st.markdown(f"**{s}**")
            else: st.info("Tidak ada sinyal Aksi...")
        with col_trend: 
            st.subheader("📊 Konteks Tren 🌊"); 
            if trend_signals:
                for s in trend_signals: st.markdown(f"**{s}**")
            else: st.info("Tren terlihat Netral...")
        st.markdown("---"); 
        with st.expander("🤔 Bingung? Klik Saya..."): st.markdown(
            """
            **Sinyal Aksi (Beli/Jual):** Cepat & Prediktif (RSI, MACD, Pola).
            **Konteks Tren (Gambaran Besar):** Lambat & Konfirmatif (MA).
            """
        )
    with col_backtest:
        st.subheader("Hasil Backtesting"); 
        strategy_options = {"MA_CROSS": "Strategi MA Cross", "MACD_TREND": "Strategi Tren MACD", "RSI_TREND": "Strategi Tren RSI (> 50)", "RSI_OVER": "Strategi RSI Overbought/Oversold"}; 
        selected_strategy_key = st.selectbox(
            "Pilih Strategi Backtest:", 
            options=list(strategy_options.keys()), 
            format_func=lambda x: strategy_options[x], 
            key="select_backtest_strategy", 
            help="Pilih strategi untuk diuji pada data historis yang ditampilkan. Ini akan mensimulasikan 'jika Anda trading dengan aturan ini'." # <-- V11.1 Tooltip
        )
        if analyzed_data is not None and not analyzed_data.empty:
            metrics_dict = backtester.run_test(analyzed_data, selected_strategy_key); 
            strat_return = metrics_dict.get('total_return_strategy', 0.0); 
            stock_return = metrics_dict.get('total_return_stock', 0.0); 
            win_rate = metrics_dict.get('win_rate', 0.0); 
            profit_factor = metrics_dict.get('profit_factor', 0.0); 
            max_drawdown = metrics_dict.get('max_drawdown', 0.0)
            st.metric(label="Pengembalian Strategi", value=f"{strat_return * 100:.2f}%", delta=f"{(strat_return - stock_return) * 100:.2f}% vs Saham", help="Total pengembalian strategi dibanding Beli & Tahan saham."); 
            col_b1, col_b2 = st.columns(2); 
            with col_b1: 
                st.metric(label="Win Rate", value=f"{win_rate * 100:.2f}%", help="Persentase trading yang profit."); 
                st.metric(label="Profit Factor", value=f"{profit_factor:.2f}" if np.isfinite(profit_factor) else "∞", help="Total profit / Total loss. >1 berarti profit.")
            with col_b2: 
                st.metric(label="Max Drawdown", value=f"{max_drawdown * 100:.2f}%", delta_color="inverse", help="Penurunan maksimum dari puncak ke lembah."); 
                st.metric(label="Pengembalian Saham (Beli & Tahan)", value=f"{stock_return * 100:.2f}%", help="Total pengembalian jika hanya membeli di awal dan menahan sampai akhir.")
        else:
            st.warning("Data tidak cukup untuk menjalankan backtesting.")

# ==========================================================
# 5. SIDEBAR (Tidak berubah)
# ==========================================================
period_interval_map = {"1 Hari": ("2d", "1m"), "1 Minggu": ("1mo", "15m"), "1 Bulan": ("3mo", "1h"), "1 Tahun": ("1y", "1d"), "Maksimal": ("max", "1wk")}
try:
    pt = PortfolioTracker() 
    wt = WatchlistTracker() 
except Exception as e:
    st.error(f"FATAL: Gagal memuat file Excel. Pastikan file 'portfolio_data.xlsx' dan 'watchlist_data.xlsx' ada dan tidak rusak. Error: {e}"); 
    st.stop()
holdings = pt.get_holdings(); 
watchlist_tickers = wt.get_watchlist(); 
tickers_in_portfolio = list(set(h['symbol'] for h in holdings)); 
current_price_dict = {}; 
if tickers_in_portfolio: 
    current_price_dict = fetch_current_prices(tickers_in_portfolio)
with st.sidebar:
    st.header("⚙️ Pengaturan Analisis Saham"); 
    st.subheader("Data Input"); 
    selected_ticker_input = st.text_input("Simbol Saham (cth: BBCA)", TICKER_DEFAULT); 
    selected_period_label = st.selectbox("Periode Data", options=list(period_interval_map.keys()), index=3); 
    selected_period, selected_interval = period_interval_map[selected_period_label]; 
    st.info(f"Interval otomatis: **{selected_interval}**"); 
    st.markdown("---")
    st.subheader("👀 Watchlist Saya")
    with st.form("tambah_watchlist"):
        wl_symbol_input = st.text_input("Simbol Saham", key="wl_add_sym", placeholder="cth: GOTO")
        submitted_wl = st.form_submit_button("Tambah ke Watchlist") 
        if submitted_wl: 
            wl_symbol = _normalize_ticker(wl_symbol_input)
            if wl_symbol and wl_symbol not in watchlist_tickers:
                wt.add_to_watchlist(wl_symbol); st.rerun() 
            elif not wl_symbol: st.warning("Simbol tidak boleh kosong.")
            else: st.info(f"{wl_symbol} sudah ada di watchlist.")
    if watchlist_tickers: 
        selected_wl_ticker = st.selectbox("Pilih Saham untuk Dihapus", options=watchlist_tickers, key="selectbox_wl_remove") 
        if st.button("Hapus dari Watchlist", key="wl_remove_btn"):
            wt.remove_from_watchlist(selected_wl_ticker); st.rerun() 
    st.markdown("---"); 
    st.subheader("💼 Portofolio Tracker"); 
    with st.form("tambah_portofolio"): 
        st.write("Tambah Saham Baru"); 
        port_symbol_input = st.text_input("Simbol", key="p_sym", placeholder="cth: ASII"); 
        port_price = st.number_input("Harga Beli (per lembar)", min_value=1.0, step=1.0, key="p_price"); 
        port_qty_lots = st.number_input("Jumlah Lot", min_value=1, step=1, key="p_qty", format="%i"); 
        submitted = st.form_submit_button("Tambah Saham")
        if submitted:
            if port_symbol_input and port_price and port_qty_lots: 
                port_symbol = _normalize_ticker(port_symbol_input); 
                port_qty_lembar = int(port_qty_lots) * 100; 
                pt.add_holding(port_symbol, port_price, port_qty_lembar); 
                st.success(f"Berhasil menambahkan {port_symbol}..."); 
                st.rerun() 
            else: st.error("Semua field harus diisi.")
    if holdings:
        st.markdown("---"); st.write("Edit/Hapus Saham"); 
        holding_options = [f"{i}: {h['symbol']} ({(h['quantity'] / 100):.0f} Lot @ Rp{h['buy_price']:,.0f})" for i, h in enumerate(holdings)]; 
        default_index = 0; 
        selected_index_str = st.selectbox("Pilih Saham", options=holding_options, index=default_index, key="select_edit_delete")
        if holding_options and selected_index_str: 
            try:
                selected_index = int(selected_index_str.split(':')[0])
                if selected_index < len(holdings):
                    selected_holding = holdings[selected_index]; 
                    col_edit_form1, col_edit_form2 = st.columns(2)
                    with col_edit_form2: 
                        if st.button("Hapus", key=f"delete_holding_{selected_index}", type="primary"): 
                            pt.remove_holding(selected_index); st.toast(f"Berhasil menghapus..."); st.rerun() 
                    with col_edit_form1:
                        with st.form(f"edit_portofolio_{selected_index}"):
                            st.write(f"Edit {selected_holding['symbol']}"); 
                            edit_symbol_input = st.text_input("Simbol Baru", value=selected_holding['symbol'].replace(".JK", ""), key="e_sym"); 
                            edit_price = st.number_input("Harga Beli Baru", min_value=1.0, step=1.0, value=float(selected_holding['buy_price']), key="e_price"); 
                            edit_qty_lots = st.number_input("Jumlah Lot Baru", min_value=1, step=1, value=int(selected_holding['quantity'] / 100), key="e_qty", format="%i"); 
                            edit_submitted = st.form_submit_button("Simpan Perubahan")
                            if edit_submitted: 
                                edit_symbol = _normalize_ticker(edit_symbol_input); 
                                edit_qty_lembar = int(edit_qty_lots) * 100; 
                                pt.update_holding(selected_index, edit_symbol, edit_price, edit_qty_lembar); 
                                st.success(f"Berhasil memperbarui..."); st.rerun() 
                else: st.warning("Item tidak lagi tersedia..."); st.rerun()
            except (ValueError, IndexError):
                 st.warning("Item tidak valid. Memuat ulang..."); st.rerun()
        else: pass 
    st.markdown("---"); 
    st.subheader("Pembaruan & Notifikasi"); 
    update_interval = 60; auto_update = True ; 
    st.info(f"Pembaruan otomatis data portofolio: {update_interval} detik.")
    if auto_update: 
        components.html(f"""<meta http-equiv="refresh" content="{update_interval}">""", height=0, width=0)
    st.sidebar.markdown("---"); 
    st.sidebar.caption("© 2025 Dibuat oleh Hendrawan Lotanto."); 
    st.sidebar.caption("Versi 4.0.0")

# ==========================================================
# 6. RUN APLIKASI UTAMA (Tidak berubah)
# ==========================================================
selected_ticker = _normalize_ticker(selected_ticker_input) 
if selected_ticker:
    start_time = time.time() ; st.info(f"⏳ Menganalisis {selected_ticker}...")
    run_analysis(selected_ticker, selected_period, selected_interval, None, current_price_dict, watchlist_tickers, pt, wt)
    end_time = time.time(); 
    st.sidebar.markdown(f"---"); 
    st.sidebar.success(f"Analisis Selesai: {end_time - start_time:.2f} detik.")
else:
    st.info("Silakan masukkan Simbol Saham di sidebar...")