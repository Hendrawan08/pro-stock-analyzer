# pages/3_🔮_Prediksi_ML.py (perbaikan)
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# --- PENTING: Impor dari root folder ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ----------------------------------------

# Cek instalasi Prophet
try:
    from prophet import Prophet
except ImportError:
    st.error("Library 'prophet' tidak ditemukan. Silakan instal: pip install prophet")
    st.stop()

try:
    from data.data_manager import fetch_data
    from constants import TICKER_DEFAULT
except ImportError:
    st.error("Gagal mengimpor modul internal. Pastikan Anda menjalankan Streamlit dari folder root.")
    st.stop()

st.set_page_config(page_title="Prediksi Harga (Prophet)", layout="wide")
st.markdown("# 🔮 Prediksi Harga Jangka Panjang (via Prophet)")
st.markdown("""
Halaman ini menggunakan model statistik **Prophet** (dari Facebook/Meta) untuk memprediksi tren harga saham.
Berbeda dengan model ML di Halaman Utama (yang memprediksi "BUY/SELL"), model ini memprediksi *pergerakan harga* dan *tren* jangka panjang.
""")
st.info("⚠️ **Peringatan:** Ini BUKAN saran finansial. Model ini hanya berdasarkan data historis dan tidak dapat memprediksi berita atau kejadian mendadak.")
st.markdown("---")

# ============================
# Helper: buat forecast (cached)
# ============================
@st.cache_data(ttl=3600, show_spinner="Menjalankan model Prophet dan membuat forecast...")
def get_prophet_forecast(ticker: str, prediction_days: int):
    """
    Mengambil data, melatih Prophet, dan mengembalikan forecast DataFrame serta history DataFrame.
    Fungsi ini di-cache dan TIDAK memanggil st.* (UI) di dalamnya.
    Return: (forecast_df, history_df) atau (None, None) bila gagal.
    """
    # Ambil data 3 tahun (kalau tersedia) -> gunakan fetch_data proyek
    data = fetch_data(ticker, "3y", "1d")
    if data is None or data.empty:
        return None, None

    # Reset index dan pastikan kita membuat kolom 'ds' (datetime) dan 'y' (Close)
    df_reset = data.reset_index()
    # Ambil kolom index pertama sebagai ds (umumnya nama index = 'Date' atau 0)
    ds_col = df_reset.columns[0]
    try:
        ds_series = pd.to_datetime(df_reset[ds_col])
    except Exception:
        # fallback: gunakan index directly
        try:
            ds_series = pd.to_datetime(data.index)
            ds_series = ds_series.to_series().reset_index(drop=True)
        except Exception:
            return None, None

    # Build df_prophet safely
    try:
        y_series = pd.to_numeric(df_reset['Close'], errors='coerce')
    except Exception:
        return None, None

    df_prophet = pd.DataFrame({'ds': ds_series, 'y': y_series})

    # Drop rows with NaN in y or ds
    df_prophet = df_prophet.dropna(subset=['ds', 'y']).reset_index(drop=True)

    # Remove timezone info if present (Prophet expects tz-naive)
    if pd.api.types.is_datetime64_any_dtype(df_prophet['ds']):
        # check tz-aware
        try:
            if df_prophet['ds'].dt.tz is not None:
                df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)
        except Exception:
            # Some pandas versions raise for tz attribute; ignore
            pass

    # Minimal data check for Prophet
    if len(df_prophet) < 30:
        return None, df_prophet  # kembalikan history untuk debug UI, tapi forecast None

    # Fit Prophet model and predict (we do NOT return model to avoid serialization issues)
    try:
        model = Prophet(
            interval_width=0.95,
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True
        )
        model.fit(df_prophet)
        future = model.make_future_dataframe(periods=prediction_days)
        forecast = model.predict(future)
        # Seri forecast adalah DataFrame yang dapat di-cache/serialize
        # Pastikan ds kolom bertipe datetime (tidy)
        forecast['ds'] = pd.to_datetime(forecast['ds'])
        return forecast, df_prophet
    except Exception:
        return None, df_prophet


# ============================
# UI Sidebar
# ============================
st.sidebar.header("Pengaturan Prediksi")
ticker_input = st.sidebar.text_input("Simbol Saham", TICKER_DEFAULT)
prediction_days = st.sidebar.slider(
    "Jumlah Hari Prediksi", min_value=7, max_value=365, value=90, step=7
)
run_button = st.sidebar.button("Jalankan Prediksi Prophet", type="primary")

st.markdown(f"### Prediksi {prediction_days} Hari ke Depan untuk **{ticker_input.upper()}**")

# ============================
# Jalankan bila user klik
# ============================
if run_button:
    with st.spinner("Menjalankan Prophet dan mengambil data..."):
        forecast, history = get_prophet_forecast(ticker_input, prediction_days)

    if forecast is None:
        if history is None or history.empty:
            st.error("Gagal mengambil data historis. Periksa simbol ticker.")
        else:
            st.error("Data tersedia, namun tidak cukup untuk menjalankan Prophet (butuh minimal ~30 bar).")
    else:
        # --- Build Plotly figure manual (yhat + CI + actual) ---
        fig = go.Figure()

        # Add predicted mean
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat'],
            mode='lines',
            name='Prediksi (yhat)',
            line=dict(color='cyan', width=2)
        ))

        # Add confidence interval: draw upper then lower with fill
        # Upper (invisible line)
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat_upper'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        # Lower, fill to previous (upper) -> creates shaded CI
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat_lower'],
            mode='lines',
            fill='tonexty',
            fillcolor='rgba(0,200,200,0.15)',
            line=dict(width=0),
            name='95% Confidence Interval'
        ))

        # Add actual historical price (if available)
        try:
            # Use history's ds and y if available, otherwise fallback to forecast where ds <= today
            hist_df = history.copy()
            # ensure ds present
            if 'ds' not in hist_df.columns:
                hist_df.reset_index(inplace=True)
                hist_df.rename(columns={hist_df.columns[0]: 'ds'}, inplace=True)
            hist_df['ds'] = pd.to_datetime(hist_df['ds'])
            fig.add_trace(go.Scatter(
                x=hist_df['ds'],
                y=hist_df['y'],
                mode='lines',
                name='Harga Aktual (historis)',
                line=dict(color='yellow', width=1)
            ))
        except Exception:
            pass

        fig.update_layout(
            title=f"Prediksi Prophet untuk {ticker_input.upper()}",
            xaxis_title="Tanggal",
            yaxis_title="Harga",
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # --- Tampilkan raw forecast table (hanya bar masa depan) ---
        st.subheader("Data Prediksi (Raw)")
        # tail prediction_days rows -> find last prediction_days rows where ds > last history ds
        try:
            last_hist_date = history['ds'].max()
            future_rows = forecast[forecast['ds'] > last_hist_date].copy()
            st.dataframe(future_rows[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].reset_index(drop=True), use_container_width=True)
        except Exception:
            st.dataframe(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(prediction_days).reset_index(drop=True), use_container_width=True)

        # --- Komponen Tren & Musiman (sederhana) ---
        st.subheader("Komponen Tren & Musiman (sederhana)")
        comp_cols = []
        # typical Prophet component names
        for name in ['trend', 'yearly', 'weekly', 'daily']:
            if name in forecast.columns:
                comp_cols.append(name)

        if comp_cols:
            # tampilkan setiap komponen sebagai plotline terhadap ds
            for c in comp_cols:
                fig_c = go.Figure()
                fig_c.add_trace(go.Scatter(x=forecast['ds'], y=forecast[c], mode='lines', name=c))
                fig_c.update_layout(title=f"Komponen: {c}", template="plotly_dark", height=300)
                st.plotly_chart(fig_c, use_container_width=True)
        else:
            st.info("Komponen tren/musiman tidak tersedia pada forecast ini.")

        st.markdown("---")
        st.info("Grafik di atas dibuat dari hasil forecast (tanpa menyimpan objek model). Jika Anda ingin menggunakan fungsi plotting resmi Prophet (`plot_plotly` atau `plot_components`), beri tahu saya — sistem akan melakukan *re-fit* model lalu memplotnya (catatan: memakan waktu lebih lama).")
else:
    st.info("Masukkan simbol ticker di sidebar dan klik 'Jalankan Prediksi Prophet' untuk memulai.")
