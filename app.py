import streamlit as st
import streamlit.components.v1 as components 
import pandas as pd
import time
import numpy as np
import plotly.graph_objects as go # <-- PERUBAHAN 1: IMPORT PLOTLY
from typing import List, Tuple, Optional 
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
from portfolio_tracker import PortfolioTracker
from visualization.plotter import PlotlyPlotter
from analysis.analyzer import fetch_and_analyze_data
from constants import * 
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
    </style>
    # 📈 Pro Stock Analyzer: Dashboard Teknikal Interaktif
    """, unsafe_allow_html=True
)

# ==========================================================
# FUNGSI UTAMA ANALISIS
# ==========================================================

def run_analysis(ticker, period, interval, auto_update_status):

    # --- VALIDASI INPUT ---
    if len(ticker) < 3 or ('.' in ticker and len(ticker.split('.')[-1]) < 2):
        st.error("⚠️ Simbol Ticker tidak valid. Mohon masukkan Simbol Saham yang benar (misalnya: GOTO.JK, TLKM.JK).")
        return

    analyzed_data = fetch_and_analyze_data(ticker, period, interval)
    
    if analyzed_data is None:
        return # Data fetching gagal (error sudah ditangani di DataManager)
        
    if analyzed_data.empty or len(analyzed_data) < 20: 
        st.warning("Data terlalu sedikit setelah perhitungan indikator. Coba periode yang lebih panjang (Minimal 20 hari/periode).")
        return

    # Inisialisasi Kelas
    signal_gen = SignalGenerator()
    plotter = PlotlyPlotter()
    backtester = Backtester()
    predictor = MLPredictor()
    
    # 3. Hasilkan Sinyal
    action_signals, trend_signals, last_data = signal_gen.generate(analyzed_data, ticker)

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

    # --- Kolom Ringkasan (Cards) --- 
    col1, col2, col3, col4, col5 = st.columns(5)
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


    # --- Grafik Interaktif (UPGRADE UI/UX dengan TABS) ---
    st.markdown("---")
    
    # ==========================================================
    # PERUBAHAN 3: TAMBAHKAN 'tab_portfolio'
    # ==========================================================
    tab_harga, tab_indikator, tab_portfolio = st.tabs([
        "📊 Grafik Utama (Harga & Volume)", 
        "📈 Indikator Momentum (RSI, MACD)",
        "💼 Portofolio Saya"
    ])
    
    with tab_harga:
        fig_price = plotter.plot_price_chart(analyzed_data, ticker)
        st.plotly_chart(fig_price, use_container_width=True, key=f"price_{str(time.time())}")
    
    with tab_indikator:
        fig_indicators = plotter.plot_indicators_chart(analyzed_data)
        st.plotly_chart(fig_indicators, use_container_width=True, key=f"indicators_{str(time.time())}")

    # ==========================================================
    # PERUBAHAN 4: TAMBAHKAN BLOK LOGIKA 'with tab_portfolio'
    # ==========================================================
    with tab_portfolio:
        st.subheader("Ringkasan Portofolio Saya")
        
        # Ambil data (holdings dan current_price_dict sudah ada dari sidebar)
        holdings = st.session_state.get(PortfolioTracker.PORTFOLIO_KEY, [])
        
        if not holdings:
            st.info("Portofolio Anda masih kosong. Silakan tambah saham pada menu di sidebar (kiri).")
        else:
            # 1. Panggil fungsi kalkulator baru dari tracker
            df_portfolio, totals = pt.calculate_portfolio_metrics(holdings, current_price_dict)
            
            # 2. Buat Layout (Ringkasan Metrik + Pie Chart)
            col_metrics, col_pie = st.columns([1, 2]) # Beri Pie Chart ruang lebih
            
            with col_metrics:
                st.metric("Total Biaya Beli", f"Rp {totals['cost']:,.0f}")
                st.metric("Total Nilai Kini", f"Rp {totals['value']:,.0f}", 
                          f"Rp {totals['pnl_rp']:,.0f} ({totals['pnl_pct']:,.2f}%)")
                with st.expander("Info Tambahan"):
                    st.write("Gunakan form di sidebar (kiri) untuk Menambah, Mengedit, atau Menghapus saham.")

            with col_pie:
                # 3. Buat Pie Chart
                pie_fig = go.Figure(data=[go.Pie(
                    labels=df_portfolio['symbol'],
                    values=df_portfolio['Value'],
                    textinfo='label+percent',
                    pull=[0.05] * len(df_portfolio), # Tarik sedikit tiap irisan
                    hole=.3 # Buat jadi Donut Chart
                )])
                pie_fig.update_layout(
                    title_text="Alokasi Aset Berdasarkan Nilai Saat Ini",
                    template="plotly_dark",
                    margin=dict(t=50, b=0, l=0, r=0),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2)
                )
                st.plotly_chart(pie_fig, use_container_width=True)
            
            st.markdown("---")
            
            # 4. Tampilkan DataFrame Detail
            st.subheader("Detail Saham")
            
            # Siapkan DataFrame untuk ditampilkan (dengan format)
            df_display = df_portfolio[[
                'symbol', 'quantity', 'buy_price', 'Current Price', 'Initial Cost', 'Value', 'PnL (Rp)', 'PnL (%)'
            ]].copy()
            
            for col in ['buy_price', 'Current Price', 'Initial Cost', 'Value', 'PnL (Rp)']:
                 df_display[col] = df_display[col].apply(lambda x: f"Rp {x:,.0f}")
            df_display['PnL (%)'] = df_display['PnL (%)'].apply(lambda x: f"{x:,.2f}%")
            
            st.dataframe(df_display, hide_index=True, use_container_width=True)


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

        st.markdown("---") # Garis pemisah
    
        with st.expander("🤔 Bingung? Klik Saya untuk Penjelasan Sinyal"):
            st.markdown(
                """
                Panel di atas dibagi menjadi dua:
    
                **1. Sinyal Aksi (Beli/Jual)**
                Ini adalah sinyal *leading* (cepat) yang memberi tahu Anda apa yang harus dilakukan **sekarang**. 
                Indikator seperti **RSI**, **MACD**, dan **Pola** masuk di sini.
    
                **2. Konteks Tren (Gambaran Besar)**
                Ini adalah sinyal *lagging* (lambat) yang memberi tahu Anda kondisi pasar secara keseluruhan.
                Indikator seperti **Moving Average (MA)** masuk di sini.
    
                **Mengapa Sinyal Bisa Bertentangan?**
                Sangat mungkin terjadi "Sinyal Aksi" (Jual) muncul saat "Konteks Tren" (Naik Kuat).
    
                * **Contoh:** "MACD Cross Down" (JUAL) + "MA Golden Cross" (NAIK KUAT).
                * **Artinya:** "Saham ini dalam tren naik jangka panjang, TAPI dalam jangka pendek momentumnya sedang turun (koreksi). **Harap Waspada!**"
                """
            )
            
    with col_backtest:
        st.subheader("Hasil Backtesting")
        
        strategy_options = {
            "MA_CROSS": "Strategi MA Cross",
            "MACD_TREND": "Strategi Tren MACD",
            "RSI_TREND": "Strategi Tren RSI (> 50)",
            "RSI_OVER": "Strategi RSI Overbought/Oversold"
        }
        
        selected_strategy_key = st.selectbox(
            "Pilih Strategi Backtest:",
            options=list(strategy_options.keys()),
            format_func=lambda x: strategy_options[x],
            key="select_backtest_strategy",
            help="Pilih strategi teknikal yang ingin Anda uji simulasikan kinerjanya di masa lalu."
        )
        
        metrics_dict = backtester.run_test(analyzed_data, selected_strategy_key) 
    
        strat_return = metrics_dict.get('total_return_strategy', 0.0)
        stock_return = metrics_dict.get('total_return_stock', 0.0)
        win_rate = metrics_dict.get('win_rate', 0.0)
        profit_factor = metrics_dict.get('profit_factor', 0.0)
        max_drawdown = metrics_dict.get('max_drawdown', 0.0)
    
        st.metric(
            label="Pengembalian Strategi",
            value=f"{strat_return * 100:.2f}%",
            delta=f"{(strat_return - stock_return) * 100:.2f}% vs Saham",
            help="Total keuntungan/kerugian dari strategi ini, dibandingkan dengan hanya membeli dan menahan saham (Beli & Tahan)."
        )
    
        col_b1, col_b2 = st.columns(2)
    
        with col_b1:
            st.metric(
                label="Win Rate",
                value=f"{win_rate * 100:.2f}%",
                help="Persentase dari total transaksi yang ditutup dengan keuntungan."
            )
            st.metric(
                label="Profit Factor",
                value=f"{profit_factor:.2f}" if np.isfinite(profit_factor) else "∞",
                help="Total untung dibagi total rugi. (Nilai > 1 bagus, < 1 buruk)."
            )
    
        with col_b2:
            st.metric(
                label="Max Drawdown",
                value=f"{max_drawdown * 100:.2f}%",
                delta_color="inverse",
                help="Kerugian maksimum dari puncak ke lembah. (Semakin kecil/mendekati 0% semakin baik)."
            )
            st.metric(
                label="Pengembalian Saham (Beli & Tahan)",
                value=f"{stock_return * 100:.2f}%",
                help="Hasil jika Anda hanya membeli saham di awal dan menjualnya di akhir."
            )

# --- AKHIR DARI FUNGSI 'run_analysis' ---


# ==========================================================
# 5. SIDEBAR UNTUK INPUT (TERMASUK FITUR PORTFOLIO TRACKER)
# ==========================================================

# Opsi Periode dan Interval (Sesuai Logika Baru Anda)
period_interval_map = {
    "1 Hari": ("1d", "1m"),
    "1 Minggu": ("1mo", "15m"), 
    "1 Bulan": ("3mo", "1h"),
    "1 Tahun": ("1y", "1d"),
    "Maksimal": ("max", "1wk")
}


with st.sidebar:
    st.header("⚙️ Pengaturan Analisis Saham")

    st.subheader("Data Input")
    selected_ticker = st.text_input("Simbol Saham (BEI)", TICKER_DEFAULT).upper()

    selected_period_label = st.selectbox(
        "Periode Data",
        options=list(period_interval_map.keys()),
        index=3 # Default ke "1 Tahun"
    )

    selected_period, selected_interval = period_interval_map[selected_period_label]

    st.info(f"Interval otomatis diatur ke: **{selected_interval}**")
    
    st.markdown("---")
    st.subheader("Portofolio Tracker")
    pt = PortfolioTracker()
    
    with st.form("tambah_portofolio"):
        st.write("Tambah Saham Baru")
        port_symbol = st.text_input("Simbol", key="p_sym").upper()
        port_price = st.number_input("Harga Beli", min_value=1.0, step=1.0, key="p_price")
        port_qty = st.number_input("Jumlah Unit", min_value=1, step=1, key="p_qty", format="%i")
        submitted = st.form_submit_button("Tambah Saham")
        
        if submitted and port_symbol and port_price and port_qty:
            pt.add_holding(port_symbol, port_price, port_qty)
            st.success(f"Berhasil menambahkan {port_symbol}.")
            st.rerun() 

    holdings = pt.get_holdings()
    
    if holdings:
        st.markdown("---")
        st.write("Edit/Hapus Saham")
        
        holding_options = [f"{i}: {h['symbol']} ({h['quantity']} @ Rp{h['buy_price']:,.0f})" for i, h in enumerate(holdings)]
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
                    edit_symbol = st.text_input("Simbol Baru", value=selected_holding['symbol'], key="e_sym").upper()
                    edit_price = st.number_input("Harga Beli Baru", min_value=1.0, step=1.0, value=selected_holding['buy_price'], key="e_price")
                    edit_qty = st.number_input("Jumlah Unit Baru", min_value=1, step=1, value=selected_holding['quantity'], key="e_qty", format="%i")
                    
                    edit_submitted = st.form_submit_button("Simpan Perubahan")
                    
                    if edit_submitted:
                        pt.update_holding(selected_index, edit_symbol, edit_price, edit_qty)
                        st.success(f"Berhasil memperbarui {edit_symbol}.")
                        st.rerun() 
        else:
            pass

    def fetch_current_prices(tickers):
        data_manager_sidebar = DataManager(None, None, None)
        price_dict = {}
        for t in tickers:
            try:
                temp_data = data_manager_sidebar.fetch_data(t, "1d", "1d") 
                if temp_data is not None and 'Close' in temp_data.columns and not temp_data.empty:
                    price_dict[t] = temp_data.iloc[-1]['Close']
                else:
                    price_dict[t] = 0.0
            except Exception:
                price_dict[t] = 0.0
        return price_dict

    tickers_in_portfolio = list(set(h['symbol'] for h in holdings))
    current_price_dict = fetch_current_prices(tickers_in_portfolio)

    # ==========================================================
    # PERUBAHAN 2: HAPUS TAMPILAN PORTFOLIO DARI SIDEBAR
    # ==========================================================
    # pt.display_portfolio(current_price_dict) <-- BARIS INI DIHAPUS

    st.markdown("---")
    st.subheader("Pembaruan & Notifikasi")
    update_interval = 60
    auto_update = True 
    
    st.info(f"Pembaruan otomatis via browser: {update_interval} detik.")
    
    if auto_update:
        components.html(
            f"""
            <meta http-equiv="refresh" content="{update_interval}">
            """,
            height=0,
            width=0,
        )


# ==========================================================
# 6. RUN APLIKASI UTAMA
# ==========================================================

if selected_ticker:
    
    start_time = time.time() 
    st.info(f"⏳ Menganalisis {selected_ticker}...")
    
    run_analysis(selected_ticker, selected_period, selected_interval, None)
    
    end_time = time.time()
    st.sidebar.markdown(f"---")
    st.sidebar.success(f"Analisis Selesai dalam **{end_time - start_time:.2f} detik**.")