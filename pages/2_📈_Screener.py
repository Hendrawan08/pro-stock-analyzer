# pages/2_📈_Screener.py

import streamlit as st
import pandas as pd
import yfinance as yf # <-- IMPORT BARU UNTUK FUNDAMENTAL
from analysis.analyzer import fetch_and_analyze_data
from constants import RSI_OVERSOLD, RSI_OVERBOUGHT

# ==========================================================
# KONFIGURASI HALAMAN
# ==========================================================
st.set_page_config(
    page_title="Screener Saham",
    layout="wide"
)

st.markdown("# 📈 Screener Saham (Teknikal & Fundamental)")
st.markdown("---")
st.warning("""
**PENTING:** Ini adalah fitur pemindaian intensif. 
- Pemindaian **Teknikal** (IDX80) mungkin memakan waktu 1-2 menit.
- Pemindaian **Fundamental** (IDX80) saat pertama kali dijalankan bisa memakan waktu **2-4 menit**.
Harap **jangan klik apapun** setelah menekan tombol "Mulai Pindai".
""", icon="⏳")


# ==========================================================
# DAFTAR SAHAM (IDX80)
# ==========================================================
IDX80_TICKERS = [
    "ACES.JK", "ADMR.JK", "ADRO.JK", "AKRA.JK", "AMRT.JK", "AMMN.JK", "ANTM.JK", 
    "ARTO.JK", "ASII.JK", "AUTO.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK", 
    "BFIN.JK", "BMRI.JK", "BRIS.JK", "BRPT.JK", "BSDE.JK", "BUKA.JK", "CERA.JK", 
    "CLEO.JK", "CLPI.JK", "CPIN.JK", "CTRA.JK", "DOOH.JK", "ESSA.JK", "EXCL.JK", 
    "GGRM.JK", "GOTO.JK", "HRUM.JK", "ICBP.JK", "INCO.JK", "INDF.JK", "INDY.JK", 
    "INKP.JK", "INTP.JK", "ISAT.JK", "ITMG.JK", "JSMR.JK", "KLBF.JK", "MAPA.JK", 
    "MAPI.JK", "MBMA.JK", "MDKA.JK", "MEDC.JK", "MIKA.JK", "MNCN.JK", "MTEL.JK", 
    "MYOR.JK", "PBSA.JK", "PGAS.JK", "PGEO.JK", "PRDA.JK", "PTBA.JK", "PTPP.JK", 
    "PWON.JK", "PYFA.JK", "SCMA.JK", "SIDO.JK", "SILO.JK", "SMGR.JK", "SMRA.JK", 
    "SRTG.JK", "SSMS.JK", "TBIG.JK", "TLKM.JK", "TOWR.JK", "TPIA.JK", "UNTR.JK", 
    "UNVR.JK", "WIIM.JK", "WIKA.JK"
]
TICKER_LIST = IDX80_TICKERS
TICKER_LIST_NAME = "IDX80"


# ==========================================================
# FUNGSI PENGAMBIL DATA FUNDAMENTAL (BARU)
# ==========================================================
@st.cache_data(ttl=3600 * 4) # Cache data fundamental selama 4 jam
def get_all_fundamental_data(ticker_list):
    """
    Mengambil data fundamental untuk semua ticker.
    Ini adalah proses yang LAMBAT dan akan di-cache.
    """
    st.info(f"Mengambil data fundamental untuk {len(ticker_list)} saham... Ini mungkin memakan waktu 2-4 menit. Data akan di-cache selama 4 jam.")
    fundamental_data = []
    progress_bar = st.progress(0, text="Memulai pengambilan data fundamental...")
    
    for i, ticker_str in enumerate(ticker_list):
        try:
            ticker = yf.Ticker(ticker_str)
            info = ticker.info
            
            # Ambil data, gunakan .get() untuk menghindari error jika key tidak ada
            data_point = {
                "Saham": ticker_str,
                "Nama Perusahaan": info.get('shortName', 'N/A'),
                "Harga": info.get('previousClose', info.get('currentPrice', 0)), # Fallback
                "P/E Ratio": info.get('trailingPE', None),
                "P/B Ratio": info.get('priceToBook', None),
                "Div. Yield (%)": info.get('dividendYield', None)
            }
            # Kalikan dividend yield agar jadi persen
            if data_point["Div. Yield (%)"] is not None:
                data_point["Div. Yield (%)"] *= 100
                
            fundamental_data.append(data_point)
        except Exception as e:
            print(f"Error mengambil info for {ticker_str}: {e}") # Log error di console
        
        progress_bar.progress((i + 1) / len(ticker_list), text=f"Menganalisis Fundamental: {ticker_str}")
        
    progress_bar.empty()
    
    df = pd.DataFrame(fundamental_data)
    # Konversi None ke NaN (Not a Number) agar bisa difilter
    df['P/E Ratio'] = pd.to_numeric(df['P/E Ratio'], errors='coerce')
    df['P/B Ratio'] = pd.to_numeric(df['P/B Ratio'], errors='coerce')
    df['Div. Yield (%)'] = pd.to_numeric(df['Div. Yield (%)'], errors='coerce')
    return df


# ==========================================================
# STRUKTUR BARU: MENGGUNAKAN TABS
# ==========================================================
st.subheader("Pilih Tipe Screener")
tab_technical, tab_fundamental = st.tabs(["⚡ Screener Teknikal", "🏦 Screener Fundamental"])


# ==========================================================
# TAB 1: SCREENER TEKNIKAL (KODE LAMA ANDA)
# ==========================================================
with tab_technical:
    st.markdown("### Atur Kriteria Pindaian Teknikal")

    # --- Kriteria Pilihan (Hanya untuk Mode Manual) ---
    criteria_options = {
        "RSI_OVERSOLD": f"RSI di Bawah {RSI_OVERSOLD} (Jenuh Jual)",
        "RSI_OVERBOUGHT": f"RSI di Atas {RSI_OVERBOUGHT} (Jenuh Beli)",
        "GOLDEN_CROSS": "Golden Cross (MA 50 > MA 100)",
        "DEATH_CROSS": "Death Cross (MA 50 < MA 100)",
        "MACD_BUY": "MACD Cross Up (Sinyal Beli)",
        "MACD_SELL": "MACD Cross Down (Sinyal Jual)",
        "NEW_DB": "Pola Double Bottom Baru",
        "NEW_DT": "Pola Double Top Baru"
    }

    # --- Opsi Periode (Berlaku untuk SEMUA mode teknikal) ---
    screener_period_map = {
        "1 Hari (Intraday)": ("2d", "1m"),
        "1 Minggu (Intraday)": ("1mo", "15m"), 
        "1 Bulan (Intraday)": ("3mo", "1h"),
        "1 Tahun (Swing)": ("1y", "1d"),
        "Maksimal (Long-term)": ("max", "1wk")
    }

    # --- Tata Letak Input ---
    col_mode, col_period = st.columns(2)
    with col_mode:
        selected_mode = st.selectbox(
            "Pilih Mode Pindaian Teknikal:",
            options=["Mode Manual", "Mode Otomatis: Top 10 Sinyal Emas"],
            index=0,
            key="tech_mode",
            help="Pilih 'Mode Manual' untuk mencari 1 kriteria spesifik, atau 'Mode Otomatis' untuk mencari sinyal beli terkuat."
        )
    with col_period:
        selected_period_label = st.selectbox(
            "Gunakan Periode Data Teknikal:",
            options=list(screener_period_map.keys()),
            index=3, # Default ke "1 Tahun (Swing)"
            key="tech_period"
        )

    selected_period_key, selected_interval = screener_period_map[selected_period_label]

    if selected_mode == "Mode Manual":
        selected_criteria = st.selectbox(
            "Cari Saham dengan Kondisi:",
            options=list(criteria_options.keys()),
            format_func=lambda x: criteria_options[x],
            key="tech_criteria"
        )
    else: # Mode Otomatis
        st.info(f"Mode Otomatis akan memindai sinyal 'Sinyal Emas' menggunakan data: **{selected_period_label}**.")

    # --- Tombol Pindai Teknikal ---
    button_label = f"Mulai Pindai Teknikal {len(TICKER_LIST)} Saham ({TICKER_LIST_NAME})"
    if st.button(button_label, type="primary", key="tech_button"):
        
        total_tickers = len(TICKER_LIST)
        progress_bar = st.progress(0, text="Memulai pemindaian teknikal...")
        
        # --- LOGIKA MODE OTOMATIS ---
        if selected_mode == "Mode Otomatis: Top 10 Sinyal Emas":
            sinyal_emas_results = []
            sinyal_macd_results = []
            
            for i, ticker in enumerate(TICKER_LIST):
                progress_text = f"Memindai ({i+1}/{total_tickers}): {ticker}..."
                progress_bar.progress((i + 1) / total_tickers, text=progress_text)
                data = fetch_and_analyze_data(ticker, selected_period_key, selected_interval)
                
                if data is None or data.empty or len(data) < 2: continue
                last, prev = data.iloc[-1], data.iloc[-2]
                
                is_macd_buy = (last['MACD'] > last['MACD_Signal']) and (prev['MACD'] < prev['MACD_Signal'])
                is_db_signal = last['DB_Signal']
                
                ticker_info = {"Saham": ticker, "Harga Penutup": last['Close'], "RSI": last['RSI'], "MACD_Hist": last['MACD_Hist']}
                
                if is_macd_buy and is_db_signal:
                    ticker_info['Sinyal'] = "🔥 EMAS (MACD + DB)"
                    sinyal_emas_results.append(ticker_info)
                elif is_macd_buy:
                    ticker_info['Sinyal'] = "🟢 MACD Buy"
                    sinyal_macd_results.append(ticker_info)

            progress_bar.empty()
            
            final_results = sinyal_emas_results
            slots_remaining = 10 - len(final_results)
            if slots_remaining > 0:
                final_results.extend([s for s in sinyal_macd_results if not any(d['Saham'] == s['Saham'] for d in final_results)][:slots_remaining])
                
            st.markdown("---")
            st.subheader(f"Hasil Pindaian: Top {len(final_results)} Sinyal Emas & MACD Buy (Periode: {selected_period_label})")
            
            if not final_results:
                st.info("Tidak ada saham yang cocok dengan kriteria 'Sinyal Emas' atau 'MACD Buy' saat ini.")
            else:
                df_results = pd.DataFrame(final_results)
                df_display = df_results.copy()
                df_display['Harga Penutup'] = df_display['Harga Penutup'].apply(lambda x: f"Rp {x:,.0f}")
                df_display['RSI'] = df_display['RSI'].apply(lambda x: f"{x:.2f}")
                df_display['MACD_Hist'] = df_display['MACD_Hist'].apply(lambda x: f"{x:.2f}")
                st.dataframe(df_display, hide_index=True, use_container_width=True)

        # --- LOGIKA MODE MANUAL ---
        elif selected_mode == "Mode Manual":
            results = []
            for i, ticker in enumerate(TICKER_LIST):
                progress_text = f"Memindai ({i+1}/{total_tickers}): {ticker}..."
                progress_bar.progress((i + 1) / total_tickers, text=progress_text)
                data = fetch_and_analyze_data(ticker, selected_period_key, selected_interval)
                
                if data is None or data.empty or len(data) < 2: continue
                last, prev = data.iloc[-1], data.iloc[-2]
                
                match = False
                if selected_criteria == "RSI_OVERSOLD": match = last['RSI'] < RSI_OVERSOLD
                elif selected_criteria == "RSI_OVERBOUGHT": match = last['RSI'] > RSI_OVERBOUGHT
                elif selected_criteria == "GOLDEN_CROSS": match = (last['MA_M'] > last['MA_L']) and (prev['MA_M'] < prev['MA_L'])
                elif selected_criteria == "DEATH_CROSS": match = (last['MA_M'] < last['MA_L']) and (prev['MA_M'] > prev['MA_L'])
                elif selected_criteria == "MACD_BUY": match = (last['MACD'] > last['MACD_Signal']) and (prev['MACD'] < prev['MACD_Signal'])
                elif selected_criteria == "MACD_SELL": match = (last['MACD'] < last['MACD_Signal']) and (prev['MACD'] > prev['MACD_Signal'])
                elif selected_criteria == "NEW_DB": match = last['DB_Signal']
                elif selected_criteria == "NEW_DT": match = last['DT_Signal']

                if match:
                    results.append({"Saham": ticker, "Harga Penutup": last['Close'], "Volume": last['Volume'], "RSI": last['RSI'], "MACD_Hist": last['MACD_Hist']})

            progress_bar.empty()
            
            st.markdown("---")
            st.subheader(f"Hasil Pindaian untuk: {criteria_options[selected_criteria]} (Periode: {selected_period_label})")
            
            if not results:
                st.info("Tidak ada saham yang cocok dengan kriteria Anda saat ini.")
            else:
                df_results = pd.DataFrame(results)
                df_display = df_results.copy()
                df_display['Harga Penutup'] = df_display['Harga Penutup'].apply(lambda x: f"Rp {x:,.0f}")
                df_display['Volume'] = df_display['Volume'].apply(lambda x: f"{x:,.0f}")
                df_display['RSI'] = df_display['RSI'].apply(lambda x: f"{x:.2f}")
                df_display['MACD_Hist'] = df_display['MACD_Hist'].apply(lambda x: f"{x:.2f}")
                st.dataframe(df_display, hide_index=True, use_container_width=True)


# ==========================================================
# TAB 2: SCREENER FUNDAMENTAL (FITUR BARU V2.0)
# ==========================================================
with tab_fundamental:
    st.markdown("### Atur Kriteria Pindaian Fundamental")
    st.markdown("Pindai saham berdasarkan valuasi dan profitabilitas. Data diambil satu kali dan di-cache selama 4 jam.")

    # --- Kontrol Input Fundamental ---
    col1, col2, col3 = st.columns(3)
    with col1:
        pe_max = st.number_input("P/E Ratio Maksimal", min_value=0.0, max_value=500.0, value=25.0, step=0.5,
                                help="Price-to-Earnings Ratio. Semakin rendah, semakin 'murah'.")
    with col2:
        pb_max = st.number_input("P/B Ratio Maksimal", min_value=0.0, max_value=50.0, value=3.0, step=0.1,
                                help="Price-to-Book Ratio. Semakin rendah, semakin 'murah'.")
    with col3:
        div_min = st.number_input("Dividend Yield Minimal (%)", min_value=0.0, max_value=25.0, value=2.0, step=0.1,
                                 help="Persentase dividen tahunan dibanding harga saham.")

    # --- Tombol Pindai Fundamental ---
    if st.button("Mulai Pindai Fundamental", type="primary", key="funda_button"):
        
        # 1. Ambil data (akan menggunakan cache jika ada)
        df_all = get_all_fundamental_data(TICKER_LIST)
        
        # 2. Filter data
        # Hapus data yang tidak memiliki P/E atau P/B (seringkali perusahaan rugi atau data tidak ada)
        df_filtered = df_all.dropna(subset=['P/E Ratio', 'P/B Ratio', 'Div. Yield (%)'])

        # Terapkan filter dari pengguna
        df_results = df_filtered[
            (df_filtered['P/E Ratio'] <= pe_max) &
            (df_filtered['P/E Ratio'] > 0) & # Pastikan P/E positif
            (df_filtered['P/B Ratio'] <= pb_max) &
            (df_filtered['P/B Ratio'] > 0) & # Pastikan P/B positif
            (df_filtered['Div. Yield (%)'] >= div_min)
        ].copy()
        
        # 3. Tampilkan Hasil
        st.markdown("---")
        st.subheader("Hasil Pindaian Fundamental")
        
        if df_results.empty:
            st.info("Tidak ada saham yang cocok dengan kriteria fundamental Anda saat ini.")
        else:
            # Format tampilan
            df_display = df_results
            df_display['Harga'] = df_display['Harga'].apply(lambda x: f"Rp {x:,.0f}")
            df_display['P/E Ratio'] = df_display['P/E Ratio'].apply(lambda x: f"{x:.2f}")
            df_display['P/B Ratio'] = df_display['P/B Ratio'].apply(lambda x: f"{x:.2f}")
            df_display['Div. Yield (%)'] = df_display['Div. Yield (%)'].apply(lambda x: f"{x:.2f}%")
            
            # Atur ulang urutan kolom
            df_display = df_display[['Saham', 'Nama Perusahaan', 'Harga', 'P/E Ratio', 'P/B Ratio', 'Div. Yield (%)']]
            
            st.dataframe(df_display, hide_index=True, use_container_width=True)

