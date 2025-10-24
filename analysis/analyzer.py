# analyzer.py
import yfinance as yf
import pandas as pd
from prophet import Prophet
import streamlit as st

# --- FUNGSI DATA DASAR ---

@st.cache_data(ttl=900, show_spinner="Mengambil info ticker...")
def get_stock_info(ticker_str: str):
    """
    Mengambil objek Ticker yfinance.
    Versi 5.0: Menambahkan try-except jika ticker tidak valid.
    """
    try:
        ticker = yf.Ticker(ticker_str)
        # Memaksa pengambilan info untuk memvalidasi
        if not ticker.info or 'symbol' not in ticker.info:
            # Kadang yfinance mengembalikan objek 'kosong'
            st.toast(f"Ticker '{ticker_str}' mungkin tidak valid atau tidak ditemukan.", icon="⚠️")
            return None
        return ticker
    except Exception as e:
        st.error(f"Gagal mengambil data yfinance untuk {ticker_str}: {e}")
        return None

@st.cache_data(ttl=900, show_spinner="Mengambil histori harga...")
def get_stock_history(ticker_obj, period: str, interval: str) -> pd.DataFrame:
    """Mengambil histori harga dari objek Ticker."""
    if ticker_obj is None:
        return pd.DataFrame() # Kembalikan DataFrame kosong
    try:
        history = ticker_obj.history(period=period, interval=interval)
        if history.empty:
            st.toast(f"Tidak ada data histori untuk periode/interval yang dipilih.", icon="ℹ️")
        return history
    except Exception as e:
        st.error(f"Gagal mengambil histori harga: {e}")
        return pd.DataFrame()

# --- FUNGSI PREDIKSI (V5.0) ---

@st.cache_data(ttl=3600, show_spinner="Membuat prediksi harga...")
def get_prophet_forecast(stock_history: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
    """
    Membuat prediksi harga menggunakan Prophet.
    Versi 5.0: Menambahkan pembersihan timezone untuk menghindari crash.
    """
    if stock_history.empty:
        return pd.DataFrame()

    try:
        # 1. Siapkan data
        df_prophet = stock_history.reset_index()[['Date', 'Close']]
        df_prophet.rename(columns={'Date': 'ds', 'Close': 'y'}, inplace=True)
        
        # 2. PERBAIKAN V5.0: Hapus Timezone (Penyebab Crash)
        # Prophet tidak suka timezone-aware datetimes.
        if pd.api.types.is_datetime64_any_dtype(df_prophet['ds']) and df_prophet['ds'].dt.tz is not None:
            df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)

        # 3. Latih Model
        # Kita nonaktifkan changepoint dan seasonality harian/mingguan jika data < 2 tahun
        daily_seasonality = 'auto'
        weekly_seasonality = 'auto'
        if len(df_prophet) < 730:
             daily_seasonality = False
             weekly_seasonality = False

        model = Prophet(
            daily_seasonality=daily_seasonality,
            weekly_seasonality=weekly_seasonality,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        model.fit(df_prophet)

        # 4. Buat Prediksi
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)
        
        return forecast
        
    except Exception as e:
        st.error(f"Gagal membuat prediksi Prophet: {e}")
        return pd.DataFrame()

# --- FUNGSI RASIO KEUANGAN (V5.0) ---

@st.cache_data(ttl=3600, show_spinner="Menghitung rasio keuangan...")
def calculate_financial_ratios(ticker_obj) -> dict:
    """
    Menghitung berbagai rasio keuangan.
    Versi 5.0: Dibuat 'Anti-Fragile'. 
    Setiap rasio dibungkus try-except agar tidak crash jika data hilang.
    """
    ratios = {}
    
    # Ambil data sekali saja
    try: info = ticker_obj.info
    except: info = {}
    try: financials = ticker_obj.financials
    except: financials = pd.DataFrame()
    try: balance_sheet = ticker_obj.balance_sheet
    except: balance_sheet = pd.DataFrame()
    
    # --- Rasio Valuasi (dari .info) ---
    
    try: ratios['Current Price (Rp)'] = info.get('currentPrice', info.get('previousClose', 0))
    except: ratios['Current Price (Rp)'] = 0
    
    try: ratios['Market Cap (Rp)'] = info.get('marketCap', 0)
    except: ratios['Market Cap (Rp)'] = 0

    try: ratios['PER (Price/Earnings Ratio)'] = info.get('trailingPE', 0)
    except: ratios['PER (Price/Earnings Ratio)'] = 0
        
    try: ratios['PBV (Price/Book Value)'] = info.get('priceToBook', 0)
    except: ratios['PBV (Price/Book Value)'] = 0

    try: ratios['Dividend Yield (%)'] = info.get('dividendYield', 0) * 100
    except: ratios['Dividend Yield (%)'] = 0

    # --- Rasio Profitabilitas (dari .financials) ---
    
    try:
        net_income = financials.loc['Net Income'].iloc[0]
        total_revenue = financials.loc['Total Revenue'].iloc[0]
        ratios['NPM (Net Profit Margin) (%)'] = (net_income / total_revenue) * 100
    except Exception:
        ratios['NPM (Net Profit Margin) (%)'] = 0 # N/A jika Total Revenue atau Net Income hilang

    # --- Rasio Solvabilitas (dari .balance_sheet) ---
    
    try:
        total_liabilities = balance_sheet.loc['Total Liabilities Net Minority Interest'].iloc[0]
        total_equity = balance_sheet.loc['Stockholders Equity'].iloc[0]
        ratios['DER (Debt to Equity Ratio)'] = total_liabilities / total_equity
    except Exception:
        ratios['DER (Debt to Equity Ratio)'] = 0 # N/A jika data hilang

    return ratios

# --- FUNGSI HELPER LAINNYA ---

@st.cache_data(ttl=300, show_spinner="Memuat harga terkini...")
def get_current_prices_for_list(ticker_list: list) -> dict:
    """
    Mengambil harga saat ini untuk daftar ticker (Portofolio/Watchlist).
    Dibuat efisien dengan satu panggilan yf.download().
    """
    price_dict = {}
    if not ticker_list:
        return price_dict
        
    try:
        # Ambil data 2 hari terakhir untuk memastikan kita mendapatkan harga penutupan terakhir
        data = yf.download(ticker_list, period='2d', interval='1d')
        
        if data.empty:
            return {ticker: 0.0 for ticker in ticker_list}
            
        # Ambil harga 'Close' terakhir yang valid
        last_prices = data['Close'].iloc[-1]
        
        if isinstance(last_prices, pd.Series):
            # Jika lebih dari 1 ticker, last_prices adalah Series
            price_dict = last_prices.to_dict()
        else:
            # Jika hanya 1 ticker, last_prices adalah float
            price_dict = {ticker_list[0]: last_prices}
            
        # Pastikan semua ticker ada di dict, beri 0 jika gagal
        for ticker in ticker_list:
            if ticker not in price_dict or pd.isna(price_dict[ticker]):
                price_dict[ticker] = 0.0
                
        return price_dict
        
    except Exception as e:
        st.warning(f"Gagal mengambil beberapa harga terkini: {e}")
        return {ticker: 0.0 for ticker in ticker_list}
