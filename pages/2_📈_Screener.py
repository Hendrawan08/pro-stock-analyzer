# pages/2_📈_Screener.py (perbaikan bagian auth)

from utils.auth import check_password
import sys
import os
from pathlib import Path

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# pastikan root project ada di sys.path (hanya sekali)
ROOT = Path(__file__).resolve().parents[1]
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)

# import internal modules (error message informatif)
try:
    from analysis.analyzer import fetch_and_analyze_data
    from constants import RSI_OVERSOLD, RSI_OVERBOUGHT, MA_MEDIUM_WINDOW, MA_LONG_WINDOW
except Exception as e:
    st.error("Gagal mengimpor modul internal. Pastikan Anda menjalankan Streamlit dari root proyek.")
    st.caption(f"Detil error import: {type(e).__name__}: {e}")
    st.stop()

# ==========================================================
# PASSWORD ANDA DI SINI
# ==========================================================

if not check_password("📈 Screener"):
    st.stop()  # Hentikan eksekusi sisa skrip jika password salah

# --- Jika lolos, lanjutkan ke konten admin ---
st.success("Password Diterima. Selamat Datang, Kreator!")

# ==========================================================

# ==========================================================
# KONFIGURASI HALAMAN
# ==========================================================
st.set_page_config(page_title="Screener & Market Overview", layout="wide")
st.markdown("# 📈 Screener & Market Overview")
st.markdown("---")

# ==========================================================
# DAFTAR SAHAM (IDX80)
# ==========================================================
IDX80_TICKERS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "MBMA.JK", "PTRO.JK", "BRPT.JK", "TLKM.JK",
    "BRMS.JK", "UNVR.JK", "BUMI.JK", "BREN.JK", "EMTK.JK", "ANTM.JK", "IMPC.JK",
    "COCO.JK", "COIN.JK", "DSSA.JK", "CDIA.JK", "BBNI.JK", "ASII.JK", "AADI.JK",
    "PIPA.JK", "AMMN.JK", "SGER.JK", "RAJA.JK", "CUAN.JK", "KLBF.JK", "ADMR.JK",
    "REAL.JK", "SMIL.JK", "MDKA.JK", "AMRT.JK", "JPFA.JK", "WIFI.JK", "ADRO.JK",
    "NCKL.JK", "ARCI.JK", "CBRE.JK", "RATU.JK", "DEWA.JK", "TOBA.JK", "JARR.JK",
    "ICBP.JK", "GTSI.JK", "HMSP.JK", "TPIA.JK", "GOTO.JK", "UNTR.JK", "ARTO.JK",
    "EMAS.JK", "BIPI.JK", "SLIS.JK", "LPKR.JK", "BRRC.JK", "ZATA.JK", "IKAN.JK",
    "BKSL.JK", "SMGA.JK", "SCMA.JK", "KIOS.JK", "WIRG.JK", "NIRO.JK", "BBYB.JK",
    "KRAS.JK", "WOWS.JK", "DOOH.JK", "ATLA.JK", "MLPL.JK", "OASA.JK", "BUKA.JK",
    "HOKI.JK", "AYAM.JK", "HUMI.JK", "ASLC.JK", "AALI.JK", "AGII.JK", "ARKO.JK",
    "AYLS.JK", "PANI.JK", "INDF.JK"
]
TICKER_LIST = IDX80_TICKERS
TICKER_LIST_NAME = "IDX80"

# ==========================================================
# FUNGSI MARKET BREADTH
# ==========================================================
@st.cache_data(ttl=900, show_spinner=f"Menganalisis Kekuatan Pasar ({TICKER_LIST_NAME})...")
def calculate_market_breadth(ticker_list):
    counts = {"above_ma50": 0, "rsi_oversold": 0, "rsi_overbought": 0, "macd_bullish": 0, "analyzed_count": 0}
    for ticker in ticker_list:
        data = fetch_and_analyze_data(ticker, "1y", "1d")
        if data is None or data.empty or len(data) < MA_MEDIUM_WINDOW:
            continue
        counts["analyzed_count"] += 1
        last = data.iloc[-1]
        # safe-get
        close = last.get('Close', None)
        ma_m = last.get('MA_M', None)
        rsi = last.get('RSI', None)
        macd = last.get('MACD', None)
        macd_sig = last.get('MACD_Signal', None)

        if close is not None and ma_m is not None and close > ma_m:
            counts["above_ma50"] += 1
        if rsi is not None and rsi < RSI_OVERSOLD:
            counts["rsi_oversold"] += 1
        if rsi is not None and rsi > RSI_OVERBOUGHT:
            counts["rsi_overbought"] += 1
        if macd is not None and macd_sig is not None and macd > macd_sig:
            counts["macd_bullish"] += 1

    valid_count = counts["analyzed_count"]
    if valid_count > 0:
        return {
            "above_ma50_pct": (counts["above_ma50"] / valid_count) * 100,
            "rsi_oversold_pct": (counts["rsi_oversold"] / valid_count) * 100,
            "rsi_overbought_pct": (counts["rsi_overbought"] / valid_count) * 100,
            "macd_bullish_pct": (counts["macd_bullish"] / valid_count) * 100,
            "analyzed_count": valid_count
        }
    else:
        return {"above_ma50_pct": 0, "rsi_oversold_pct": 0, "rsi_overbought_pct": 0, "macd_bullish_pct": 0, "analyzed_count": 0}

# ==========================================================
# FUNGSI DATA HEATMAP (V10.5 - DIPERBAIKI)
#  -> Tidak membuat widget UI di dalam fungsi cached
# ==========================================================
@st.cache_data(ttl=900, show_spinner="Memuat data Heatmap (pertama kali akan lambat)...")
def get_heatmap_data(ticker_list):
    """
    Mengambil Sektor, Kap. Pasar, dan % Ubah Harian untuk Treemap.
    Return: DataFrame dengan kolom ['Saham','Sektor','Kap. Pasar','Ubah %']
    'Ubah %' sudah dalam persen (mis. 1.23 = 1.23%).
    """
    heatmap_data = []
    for ticker_str in ticker_list:
        try:
            t = yf.Ticker(ticker_str)
            info = t.info or {}
            # get change percent robustly
            change_pct_raw = info.get('regularMarketChangePercent', None)
            # if not present, compute from previousClose & regularMarketPrice or currentPrice
            if change_pct_raw is None:
                prev_close = info.get('previousClose', None)
                current_price = info.get('regularMarketPrice', info.get('currentPrice', None))
                if prev_close and current_price and prev_close != 0:
                    change_pct = ((current_price - prev_close) / prev_close) * 100.0
                else:
                    change_pct = 0.0
            else:
                # normalize: if raw looks like fraction (abs <=1) -> multiply by 100, else treat as percent already
                try:
                    change_pct = float(change_pct_raw)
                    if abs(change_pct) <= 1.0:
                        change_pct = change_pct * 100.0
                except Exception:
                    change_pct = 0.0

            sector = info.get('sector') or "Lainnya"
            market_cap = info.get('marketCap') or 0
            # only include if market_cap positive (to size treemap)
            if isinstance(market_cap, (int, float)) and market_cap > 0:
                heatmap_data.append({
                    "Saham": ticker_str,
                    "Sektor": sector,
                    "Kap. Pasar": market_cap,
                    "Ubah %": change_pct
                })
        except Exception:
            # silent fail for individual tickers — cached function shouldn't print widgets
            continue

    df = pd.DataFrame(heatmap_data)
    return df

# ==========================================================
# UI MARKET OVERVIEW (BREADTH & HEATMAP)
# ==========================================================
st.markdown("## Gambaran Pasar Saat Ini (IDX80)")
st.caption("Data diperbarui setiap 15 menit.")

# --- 1. Market Breadth ---
breadth_data = calculate_market_breadth(TICKER_LIST)
if breadth_data["analyzed_count"] == 0:
    st.warning("Tidak dapat menghitung gambaran pasar. Gagal mengambil data saham.")
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label=f"% Saham > MA{MA_MEDIUM_WINDOW}",
            value=f"{breadth_data['above_ma50_pct']:.1f}%",
            help=f"Persentase saham IDX80 yang harga penutup terakhirnya di atas Moving Average {MA_MEDIUM_WINDOW} hari."
        )
    with col2:
        st.metric(
            label="% Saham MACD Bullish",
            value=f"{breadth_data['macd_bullish_pct']:.1f}%",
            help="Persentase saham IDX80 yang garis MACD-nya berada di atas garis sinyal MACD."
        )
    with col3:
        st.metric(
            label=f"% Saham Oversold (RSI < {RSI_OVERSOLD})",
            value=f"{breadth_data['rsi_oversold_pct']:.1f}%",
            help=f"Persentase saham IDX80 yang memasuki area jenuh jual (RSI < {RSI_OVERSOLD}).",
            delta_color="off"
        )
    with col4:
        st.metric(
            label=f"% Saham Overbought (RSI > {RSI_OVERBOUGHT})",
            value=f"{breadth_data['rsi_overbought_pct']:.1f}%",
            help=f"Persentase saham IDX80 yang memasuki area jenuh beli (RSI > {RSI_OVERBOUGHT}).",
            delta_color="off"
        )

    st.caption(f"Berdasarkan analisis {breadth_data['analyzed_count']} dari {len(TICKER_LIST)} saham IDX80 menggunakan data harian.")
    st.markdown("---")

# --- 2. Heatmap/Treemap ---
st.markdown("### 🗺️ Heatmap Pasar (IDX80)")
st.caption("Ukuran kotak berdasarkan Kapitalisasi Pasar. Warna berdasarkan % Perubahan Harian.")

# show spinner while loading heavy operation (call cached function)
with st.spinner("Mengambil data untuk heatmap (sekitar 30-60 detik, tergantung koneksi)..."):
    df_heatmap = get_heatmap_data(TICKER_LIST)

if df_heatmap.empty:
    st.warning("Gagal memuat data heatmap. Coba refresh setelah beberapa saat.")
else:
    # Build treemap nodes: first unique sectors, then tickers
    sectors = sorted(df_heatmap['Sektor'].unique())
    sector_caps = df_heatmap.groupby('Sektor')['Kap. Pasar'].sum().to_dict()

    labels = []
    parents = []
    values = []
    colors = []

    # add sector (root) nodes
    for sec in sectors:
        labels.append(sec)
        parents.append("")            # root
        values.append(sector_caps.get(sec, 0))
        colors.append(0)              # neutral color for sector nodes

    # add ticker nodes (child of sector)
    for _, row in df_heatmap.iterrows():
        labels.append(row['Saham'])
        parents.append(row['Sektor'])
        values.append(row['Kap. Pasar'])
        # color = percent change (already in percent)
        colors.append(row['Ubah %'])

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            colorscale='RdYlGn',
            cmid=0,
            showscale=True,
            colorbar=dict(title="% Ubah")
        ),
        hovertemplate="<b>%{label}</b><br>Parent: %{parent}<br>Kap. Pasar: %{value:,.0f}<br>Ubah %: %{color:.2f}%<extra></extra>",
        textinfo="label+value",
        root_color="lightgrey"
    ))

    fig.update_layout(margin=dict(t=25, l=10, r=10, b=10), height=600)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================================
# FUNGSI FUNDAMENTAL (TAK ADA UI DI DALAM cached FUNCTION)
# ==========================================================
@st.cache_data(ttl=3600 * 4)
def get_all_fundamental_data(ticker_list):
    fundamental_data = []
    for ticker_str in ticker_list:
        try:
            t = yf.Ticker(ticker_str)
            info = t.info or {}
            data_point = {
                "Saham": ticker_str,
                "Nama Perusahaan": info.get('shortName', 'N/A'),
                "Harga": info.get('previousClose', info.get('currentPrice', 0)),
                "P/E Ratio": info.get('trailingPE', None),
                "P/B Ratio": info.get('priceToBook', None),
                "Div. Yield (%)": info.get('dividendYield', None)
            }
            if data_point["Div. Yield (%)"] is not None:
                data_point["Div. Yield (%)"] = data_point["Div. Yield (%)"] * 100.0
            fundamental_data.append(data_point)
        except Exception:
            continue
    df = pd.DataFrame(fundamental_data)
    if not df.empty:
        df['P/E Ratio'] = pd.to_numeric(df['P/E Ratio'], errors='coerce')
        df['P/B Ratio'] = pd.to_numeric(df['P/B Ratio'], errors='coerce')
        df['Div. Yield (%)'] = pd.to_numeric(df['Div. Yield (%)'], errors='coerce')
    return df

# ==========================================================
# TABS (Screener Kustom & Fundamental)
# ==========================================================
st.subheader("Pilih Tipe Screener")
tab_technical, tab_fundamental = st.tabs(["🔍 Screener Teknikal Kustom", "🏦 Screener Fundamental"])

# =Lanjutan: TAB 1 (Teknikal) & TAB 2 (Fundamental) ...
with tab_technical:
    st.markdown("### Bangun Aturan Pindaian Teknikal Anda")
    st.markdown("Pilih filter yang ingin Anda gunakan. Data harian ('1y', '1d') akan digunakan untuk pemindaian.")
    st.markdown("---")

    with st.form(key="custom_screener_form"):
        filter_logic = st.radio("Pilih logika filter:", ("Penuhi SEMUA kriteria (AND)", "Penuhi SALAH SATU kriteria (OR)"), index=0, key="filter_logic")
        st.markdown("---")
        st.markdown("**2. Pilih Filter Teknikal (Aktifkan untuk menggunakan)**")
        active_filters = []
        cols_1, cols_2 = st.columns(2)
        with cols_1:
            st.markdown("##### Filter RSI")
            use_rsi = st.checkbox("Aktifkan Filter RSI", key="use_rsi")
            rsi_min = st.number_input("RSI Minimal", 0, 100, 0, key="rsi_min")
            rsi_max = st.number_input("RSI Maksimal", 0, 100, 30, key="rsi_max")
            if use_rsi:
                # use lambda that expects eval_data {'last':Series}
                active_filters.append(lambda d, lo=rsi_min, hi=rsi_max: (d['last'].get('RSI', 999) >= lo) and (d['last'].get('RSI', 0) <= hi))

            st.markdown("##### Filter MACD")
            use_macd = st.checkbox("Aktifkan Filter MACD", key="use_macd")
            macd_cond = st.selectbox("Pilih kondisi MACD:", ["(Tidak aktif)", "MACD > Signal (Bullish)", "MACD < Signal (Bearish)", "Baru Cross Up", "Baru Cross Down"], key="macd_cond")
            if use_macd and macd_cond != "(Tidak aktif)":
                if macd_cond == "MACD > Signal (Bullish)":
                    active_filters.append(lambda d: d['last'].get('MACD', 0) > d['last'].get('MACD_Signal', 1))
                elif macd_cond == "MACD < Signal (Bearish)":
                    active_filters.append(lambda d: d['last'].get('MACD', 0) < d['last'].get('MACD_Signal', 0))
                elif macd_cond == "Baru Cross Up":
                    active_filters.append(lambda d: (d['last'].get('MACD', 0) > d['last'].get('MACD_Signal', 0)) and (d['prev'].get('MACD', 0) <= d['prev'].get('MACD_Signal', 0)))
                elif macd_cond == "Baru Cross Down":
                    active_filters.append(lambda d: (d['last'].get('MACD', 0) < d['last'].get('MACD_Signal', 0)) and (d['prev'].get('MACD', 0) >= d['prev'].get('MACD_Signal', 0)))

        with cols_2:
            st.markdown("##### Filter Moving Average (MA)")
            use_ma = st.checkbox("Aktifkan Filter MA", key="use_ma")
            ma_cond = st.selectbox("Pilih kondisi MA:", ["(Tidak aktif)", f"Harga > MA {MA_MEDIUM_WINDOW}", f"Harga < MA {MA_MEDIUM_WINDOW}", f"MA {MA_MEDIUM_WINDOW} > MA {MA_LONG_WINDOW} (Golden)", f"MA {MA_MEDIUM_WINDOW} < MA {MA_LONG_WINDOW} (Death)"], key="ma_cond")
            if use_ma and ma_cond != "(Tidak aktif)":
                if ma_cond == f"Harga > MA {MA_MEDIUM_WINDOW}":
                    active_filters.append(lambda d: d['last'].get('Close', 0) > d['last'].get('MA_M', 1))
                elif ma_cond == f"Harga < MA {MA_MEDIUM_WINDOW}":
                    active_filters.append(lambda d: d['last'].get('Close', 0) < d['last'].get('MA_M', 0))
                elif ma_cond == f"MA {MA_MEDIUM_WINDOW} > MA {MA_LONG_WINDOW} (Golden)":
                    active_filters.append(lambda d: d['last'].get('MA_M', 0) > d['last'].get('MA_L', 0))
                elif ma_cond == f"MA {MA_MEDIUM_WINDOW} < MA {MA_LONG_WINDOW} (Death)":
                    active_filters.append(lambda d: d['last'].get('MA_M', 0) < d['last'].get('MA_L', 0))

            st.markdown("##### Filter Volume")
            use_vol = st.checkbox("Aktifkan Filter Volume", key="use_vol")
            vol_mult = st.number_input("Volume > (x) * Rata-rata 20 Hari", min_value=1.0, step=0.1, value=1.5, key="vol_mult")
            if use_vol:
                # use safe-get => if Volume_MA20 missing -> treat as 0
                active_filters.append(lambda d, m=vol_mult: (d['last'].get('Volume', 0) > (d['last'].get('Volume_MA20', 0) * m)))

        st.markdown("---")
        submit_button = st.form_submit_button(label="Mulai Pindai Kustom", type="primary")
        st.caption("Catatan: Pemindaian akan membutuhkan waktu (± 1-2 menit untuk 80 saham).")

    if submit_button:
        if not active_filters:
            st.error("Anda belum mengaktifkan filter apa pun. Centang setidaknya satu kotak 'Aktifkan Filter'.")
            if 'screener_results' in st.session_state:
                del st.session_state['screener_results']
        else:
            st.markdown("---")
            st.subheader(f"Hasil Pindaian Kustom (Logika: {filter_logic.split(' ')[1]})")
            total_tickers = len(TICKER_LIST)
            progress = st.progress(0)
            results_list = []
            for i, ticker in enumerate(TICKER_LIST):
                progress.progress(int((i + 1) / total_tickers * 100))
                data = fetch_and_analyze_data(ticker, "1y", "1d")
                if data is None or data.empty or len(data) < 2:
                    continue
                eval_data = {"last": data.iloc[-1], "prev": data.iloc[-2]}
                eval_results = []
                for f in active_filters:
                    try:
                        eval_results.append(bool(f(eval_data)))
                    except Exception:
                        eval_results.append(False)
                is_match = (all(eval_results) if filter_logic.startswith("Penuhi SEMUA") else any(eval_results))
                if is_match:
                    last_row = eval_data['last']
                    results_list.append({"Saham": ticker, "Harga": last_row.get('Close', 0.0), "Momentum 10D (%)": last_row.get('Change_10D', 0.0)})
            progress.empty()
            df_results = pd.DataFrame(results_list)
            st.session_state['screener_results'] = df_results
            if df_results.empty:
                st.info("Tidak ada saham yang cocok dengan kriteria filter Anda saat ini.")
            else:
                st.success(f"Ditemukan {len(df_results)} saham yang cocok:")

    # Tampilkan hasil (jika ada)
    if 'screener_results' in st.session_state:
        df_results = st.session_state['screener_results']
        if not df_results.empty:
            sort_by = st.selectbox("Urutkan hasil berdasarkan:", ("Momentum 10D (Tertinggi)", "Momentum 10D (Terendah)", "Saham (A-Z)"), index=0, key="sorter")
            if sort_by == "Momentum 10D (Tertinggi)":
                df_sorted = df_results.sort_values(by="Momentum 10D (%)", ascending=False)
            elif sort_by == "Momentum 10D (Terendah)":
                df_sorted = df_results.sort_values(by="Momentum 10D (%)", ascending=True)
            else:
                df_sorted = df_results.sort_values(by="Saham", ascending=True)
            df_display = df_sorted.copy()
            df_display['Harga'] = df_display['Harga'].apply(lambda x: f"Rp {x:,.0f}")
            df_display['Momentum 10D (%)'] = df_display['Momentum 10D (%)'].apply(lambda x: f"{x:+.2f}%")
            st.dataframe(df_display.reset_index(drop=True), use_container_width=True, hide_index=True)

with tab_fundamental:
    st.markdown("### Atur Kriteria Pindaian Fundamental")
    st.markdown("Pindai saham berdasarkan valuasi dan profitabilitas. Data diambil satu kali dan di-cache selama 4 jam.")
    with st.form(key="funda_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            pe_max = st.number_input("P/E Ratio Maksimal", min_value=0.0, max_value=500.0, value=25.0, step=0.5)
        with col2:
            pb_max = st.number_input("P/B Ratio Maksimal", min_value=0.0, max_value=50.0, value=3.0, step=0.1)
        with col3:
            div_min = st.number_input("Dividend Yield Minimal (%)", min_value=0.0, max_value=25.0, value=2.0, step=0.1)
        funda_submit = st.form_submit_button("Mulai Pindai Fundamental", type="primary")

    if funda_submit:
        with st.spinner("Mengambil data fundamental..."):
            df_all = get_all_fundamental_data(TICKER_LIST)
        df_filtered = df_all.dropna(subset=['P/E Ratio', 'P/B Ratio', 'Div. Yield (%)']) if not df_all.empty else pd.DataFrame()
        df_results = df_filtered[
            (df_filtered['P/E Ratio'] <= pe_max) & (df_filtered['P/E Ratio'] > 0) &
            (df_filtered['P/B Ratio'] <= pb_max) & (df_filtered['P/B Ratio'] > 0) &
            (df_filtered['Div. Yield (%)'] >= div_min)
        ].copy()
        st.markdown("---")
        st.subheader("Hasil Pindaian Fundamental")
        if df_results.empty:
            st.info("Tidak ada saham yang cocok dengan kriteria fundamental Anda saat ini.")
        else:
            df_display = df_results.copy()
            df_display['Harga'] = df_display['Harga'].apply(lambda x: f"Rp {x:,.0f}")
            df_display['P/E Ratio'] = df_display['P/E Ratio'].apply(lambda x: f"{x:.2f}")
            df_display['P/B Ratio'] = df_display['P/B Ratio'].apply(lambda x: f"{x:.2f}")
            df_display['Div. Yield (%)'] = df_display['Div. Yield (%)'].apply(lambda x: f"{x:.2f}%")
            df_display = df_display[['Saham', 'Nama Perusahaan', 'Harga', 'P/E Ratio', 'P/B Ratio', 'Div. Yield (%)']]
            st.dataframe(df_display, hide_index=True, use_container_width=True)
