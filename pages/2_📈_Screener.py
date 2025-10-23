# pages/2_📈_Screener.py

import streamlit as st
import pandas as pd
from analysis.analyzer import fetch_and_analyze_data # <-- Impor fungsi inti kita
from constants import RSI_OVERSOLD, RSI_OVERBOUGHT # <-- Impor konstanta

# ==========================================================
# KONFIGURASI HALAMAN
# ==========================================================
st.set_page_config(
    page_title="Screener Saham",
    layout="wide"
)

st.markdown("# 📈 Screener Saham (Penyaring Peluang)")
st.markdown("---")
st.warning("""
**PENTING:** Ini adalah fitur pemindaian intensif dan mungkin memakan waktu 1-2 menit. 
Harap **jangan klik apapun** setelah menekan tombol "Mulai Pindai".
""", icon="⏳")


# ==========================================================
# DAFTAR SAHAM (Kita mulai dengan LQ45 agar cepat)
# ==========================================================
# Di masa depan, Anda bisa mengganti ini dengan daftar dari "IDX30", "IDX80", atau "KOMPAS100"
LQ45_TICKERS = [
    "ADRO.JK", "AKRA.JK", "AMRT.JK", "ANTM.JK", "ARTO.JK", "ASII.JK", "BBCA.JK",
    "BBNI.JK", "BBRI.JK", "BBTN.JK", "BMRI.JK", "BRIS.JK", "BRPT.JK", "BUKA.JK",
    "CPIN.JK", "ESSA.JK", "EXCL.JK", "GOTO.JK", "HRUM.JK", "ICBP.JK", "INCO.JK",
    "INDF.JK", "INDY.JK", "INKP.JK", "INTP.JK", "ITMG.JK", "KLBF.JK", "MAPI.JK",
    "MBMA.JK", "MDKA.JK", "MEDC.JK", "MTEL.JK", "PGAS.JK", "PGEO.JK", "PTBA.JK",
    "PTG.JK", "SIDO.JK", "SMGR.JK", "SRTG.JK", "TBIG.JK", "TLKM.JK", "TOWR.JK",
    "TPIA.JK", "UNTR.JK", "UNVR.JK"
]


# ==========================================================
# KONTROL INPUT PENGGUNA
# ==========================================================
st.subheader("Atur Kriteria Pindaian Anda")

# --- Kriteria Pilihan ---
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

# --- Periode Pilihan ---
# Untuk screener, kita butuh data lebih banyak. Default ke '1y' (1 Tahun)
# agar MA 50 dan MA 100 bisa dihitung.
screener_period_options = {
    "6mo": "6 Bulan (Interval 1d)",
    "1y": "1 Tahun (Interval 1d)",
    "max": "Maksimal (Interval 1wk)"
}

col_crit, col_period = st.columns(2)

with col_crit:
    selected_criteria = st.selectbox(
        "Cari Saham dengan Kondisi:",
        options=list(criteria_options.keys()),
        format_func=lambda x: criteria_options[x]
    )
with col_period:
    selected_period_key = st.selectbox(
        "Gunakan Data Periode:",
        options=list(screener_period_options.keys()),
        index=1 # Default ke "1 Tahun"
    )

# Tentukan interval berdasarkan periode
selected_interval = "1wk" if selected_period_key == "max" else "1d"


# ==========================================================
# LOGIKA INTI SCREENER (Tombol & Pemindaian)
# ==========================================================

if st.button(f"Mulai Pindai {len(LQ45_TICKERS)} Saham (LQ45)", type="primary"):
    
    results = []
    total_tickers = len(LQ45_TICKERS)
    
    # Tampilkan progress bar
    progress_bar = st.progress(0, text="Memulai pemindaian...")
    
    for i, ticker in enumerate(LQ45_TICKERS):
        # Update progress bar
        progress_text = f"Memindai ({i+1}/{total_tickers}): {ticker}..."
        progress_bar.progress((i + 1) / total_tickers, text=progress_text)
        
        # 1. Ambil dan analisis data
        # Kita pakai periode dan interval yang dipilih pengguna
        data = fetch_and_analyze_data(ticker, selected_period_key, selected_interval)
        
        # Jika data gagal di-load (misal: saham baru) atau NaN, lewati
        if data is None or data.empty:
            continue
            
        # 2. Ambil data baris terakhir untuk dicek
        last = data.iloc[-1]
        
        # 3. Cek kondisi kriteria
        match = False
        if selected_criteria == "RSI_OVERSOLD":
            if last['RSI'] < RSI_OVERSOLD:
                match = True
        elif selected_criteria == "RSI_OVERBOUGHT":
            if last['RSI'] > RSI_OVERBOUGHT:
                match = True
        elif selected_criteria == "GOLDEN_CROSS":
            # Cek data 2 hari terakhir untuk cross
            prev = data.iloc[-2]
            if (last['MA_M'] > last['MA_L']) and (prev['MA_M'] < prev['MA_L']):
                match = True
        elif selected_criteria == "DEATH_CROSS":
            prev = data.iloc[-2]
            if (last['MA_M'] < last['MA_L']) and (prev['MA_M'] > prev['MA_L']):
                match = True
        elif selected_criteria == "MACD_BUY":
            prev = data.iloc[-2]
            if (last['MACD'] > last['MACD_Signal']) and (prev['MACD'] < prev['MACD_Signal']):
                match = True
        elif selected_criteria == "MACD_SELL":
            prev = data.iloc[-2]
            if (last['MACD'] < last['MACD_Signal']) and (prev['MACD'] > prev['MACD_Signal']):
                match = True
        elif selected_criteria == "NEW_DB":
            if last['DB_Signal']:
                match = True
        elif selected_criteria == "NEW_DT":
            if last['DT_Signal']:
                match = True

        # 4. Jika cocok, tambahkan ke hasil
        if match:
            results.append({
                "Saham": ticker,
                "Harga Penutup": last['Close'],
                "Volume": last['Volume'],
                "RSI": last['RSI'],
                "MACD_Hist": last['MACD_Hist']
            })

    # Selesai Pindai
    progress_bar.empty() # Hapus progress bar

    # ==========================================================
    # TAMPILKAN HASIL
    # ==========================================================
    
    st.markdown("---")
    st.subheader(f"Hasil Pindaian untuk: {criteria_options[selected_criteria]}")
    
    if not results:
        st.info("Tidak ada saham yang cocok dengan kriteria Anda saat ini.")
    else:
        df_results = pd.DataFrame(results)
        
        # Format tampilan
        df_display = df_results.copy()
        df_display['Harga Penutup'] = df_display['Harga Penutup'].apply(lambda x: f"Rp {x:,.0f}")
        df_display['Volume'] = df_display['Volume'].apply(lambda x: f"{x:,.0f}")
        df_display['RSI'] = df_display['RSI'].apply(lambda x: f"{x:.2f}")
        df_display['MACD_Hist'] = df_display['MACD_Hist'].apply(lambda x: f"{x:.2f}")

        st.dataframe(df_display, hide_index=True, use_container_width=True)