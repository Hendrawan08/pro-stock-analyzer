import streamlit as st

# ==========================================================
# KONFIGURASI HALAMAN
# ==========================================================
st.set_page_config(
    page_title="Pusat Pengetahuan",
    layout="wide"
)

st.title("🎓 Pusat Pengetahuan V3.0.0") # <-- Versi diperbarui
st.markdown("---")

# ==========================================================
# BAGIAN 1: CATATAN RILIS (CHANGELOG) - (DIPERBARUI!)
# ==========================================================
st.header("Bagian 1: Catatan Rilis (Changelog)")
st.markdown("Lihat apa saja yang baru di Pro Stock Analyzer!")

with st.expander("Versi 3.0.0 (15 Okt 2025) - Database Permanen (BARU!)"):
    st.markdown("""
    - **DATABASE PERMANEN (V3.0)!** Ini adalah upgrade arsitektur terbesar.
    - **Data Tersimpan:** Portofolio dan Watchlist Anda sekarang disimpan di database cloud (Supabase) yang aman, bukan di `st.session_state`.
    - **Tidak Hilang Lagi:** Data Anda **TIDAK AKAN HILANG** lagi saat Anda me-refresh (F5) browser atau menutup aplikasi. Anda bisa mengaksesnya kapan saja.
    - **Integrasi `st.connection`:** Menulis ulang total file `portfolio_tracker.py` dan `watchlist_tracker.py` untuk menggunakan `st.connection` dan SQL.
    - **UI Polish:** Mengganti nama `app.py` menjadi `1_📊_Analisis_Utama.py` agar terlihat profesional di sidebar.
    """)

with st.expander("Versi 2.1.1 (14 Okt 2025) - Input Polish"):
    st.markdown("""
    - **Input Ticker Fleksibel:** Anda sekarang bisa mengetik `BBCA` atau `bbca` (tanpa `.JK`) di semua form input.
    - **Sistem Portofolio per LOT:** Semua input di Portofolio Tracker sekarang menggunakan **LOT** (1 Lot = 100 Lembar).
    - **Perbaikan Bug Kritis:** Memperbaiki `KeyError` di Tab Watchlist.
    """)

with st.expander("Versi 2.1.0 (13 Okt 2025) - Mobile Polish"):
    st.markdown("""
    - **UI Mobile-Friendly:** Merombak total tampilan di halaman utama (`app.py`).
    - **"Result Cards":** Menghapus semua `st.dataframe` yang tidak ramah HP dan menggantinya dengan "Kartu Hasil".
    - **Grafik Interaktif (Sentuh):** Meng-upgrade semua grafik agar mendukung "Pan" (Geser) dan "Pinch-to-Zoom" (Cubit).
    - **Perbaikan Bug ML Dinamis:** Memperbaiki bug "Akurasi 47.8%" yang selalu sama.
    """)

with st.expander("Versi 2.0.0 (12 Okt 2025) - Fitur Fundamental"):
    st.markdown("""
    - **Screener Fundamental:** Menambahkan Tab "Screener Fundamental" (P/E, P/B, Dividen) di halaman Screener.
    """)

with st.expander("Versi 1.0.0 - 1.2.0 (Rilis Awal)"):
     st.markdown("""
    - **Analisis Multi-Timeframe (MTA):** Menambahkan panel MTA di halaman utama.
    - **Watchlist & Mini-Dashboard:** Menambahkan Tab "Watchlist Saya".
    - **Screener Teknikal:** Menambahkan "Top 10 Sinyal Emas" dan daftar IDX80.
    - **Fitur Inti:** Grafik, Indikator, Backtesting, dan Portofolio (V1 awal).
    """)

# ==========================================================
# BAGIAN 2: KONFLIK SINYAL (PALING PENTING)
# ==========================================================
st.header("Bagian 2: Konflik Sinyal - 'Peta' vs 'GPS'")
st.markdown("""
Konflik sinyal adalah hal paling umum dalam analisis teknikal. Ini **bukan bug**, 
melainkan aplikasi yang menunjukkan pertarungan antara gambaran besar (Peta) dan 
momentum jangka pendek (GPS).

Aturan utamanya: **Selalu prioritaskan Peta (Pola Jangka Panjang), dan gunakan GPS (Momentum) hanya untuk mencari waktu masuk (konfirmasi).**
""")

with st.expander("Studi Kasus 1: Pola Double Top (SELL) 🔴 vs MACD (BUY) 🟢"):
    st.markdown("""
    Ini adalah skenario paling berbahaya, sering disebut **"Bull Trap" (Jebakan Banteng)**.
    
    * **Apa yang Terjadi?** Harga sedang dalam proses naik untuk membentuk "Puncak ke-2". Karena harga sedang naik dalam jangka pendek, wajar jika MACD (GPS) memberi sinyal "BUY".
    * **Pola (Peta) Berkata:** "Hati-hati! Ini adalah area puncak tebing. Bersiap untuk Jual."
    * **Momentum (GPS) Berkata:** "Beli! Harga sedang naik!"
    * **Rekomendasi:** **JANGAN BELI (SANGAT BERISIKO).** 🔴
    * **Cara Membaca:** Sinyal Beli dari MACD ini adalah *palsu*. Ini adalah reli terakhir yang memancing pembeli baru masuk tepat setelah harga berbalik arah turun.
    """)

with st.expander("Studi Kasus 2: Pola Double Bottom (BUY) 🟢 vs MACD (SELL) 🔴"):
    st.markdown("""
    Ini adalah skenario paling umum saat menunggu konfirmasi.
    
    * **Apa yang Terjadi?** Harga *baru saja jatuh* untuk membentuk "Lembah ke-2" (bagian akhir dari huruf 'W'). Karena harga baru saja jatuh, wajar jika MACD (GPS) masih memberi sinyal "SELL".
    * **Pola (Peta) Berkata:** "Area support kuat! Bersiap Beli!"
    * **Momentum (GPS) Berkata:** "Jual! Momentum masih negatif!"
    * **Rekomendasi:** **TUNGGU KONFIRMASI (JANGAN BELI DULU).** ⚠️
    * **Cara Membaca:** Peta Anda sudah benar, tapi GPS Anda belum siap. Trader pro akan **menunggu** sampai MACD juga *cross up* (memberi sinyal BUY). Itulah konfirmasi Anda untuk masuk.
    """)

# ==========================================================
# BAGIAN 3: SKENARIO IDEAL
# ==========================================================
st.header("Bagian 3: Skenario Ideal - Sinyal Konfirmasi")
with st.expander("Sinyal Emas: Pola Double Bottom (BUY) 🟢 + MACD (BUY) 🟢"):
    st.markdown("""
    Inilah yang dicari semua trader.
    
    * **Pola (Peta) Berkata:** "Kita di support kuat, siap naik!"
    * **Momentum (GPS) Berkata:** "Kita sudah berbalik arah, ayo naik!"
    * **Cara Membaca:** Ini adalah sinyal beli dengan probabilitas keberhasilan tertinggi. Peta dan GPS Anda setuju. Inilah yang dicari oleh "Mode Otomatis: Top 10 Sinyal Emas" di Screener Teknikal.
    """)
    
# ==========================================================
# BAGIAN 4: PERAN INDIKATOR TEKNIKAL
# ==========================================================
st.header("Bagian 4: Peran Indikator Teknikal")

with st.expander("Indikator Momentum (MACD, RSI, Stochastic) - 'GPS' Jangka Pendek"):
    st.markdown("""
    Indikator ini adalah **Leading (Memimpin)**. Mereka mencoba memprediksi apa yang akan terjadi selanjutnya 
    dengan mengukur "kekuatan" atau "kecepatan" di balik pergerakan harga.
    
    * **MACD:** Mengukur momentum Beli vs Jual.
    * **RSI & Stochastic:** Mengukur kejenuhan pasar (Overbought/Oversold).
    * **Kekuatan:** Sangat cepat memberi sinyal.
    * **Kelemahan:** Sering memberi sinyal palsu.
    """)

with st.expander("Indikator Tren (Moving Average/MA) - 'Konteks' Jangka Panjang"):
    st.markdown("""
    Indikator ini adalah **Lagging (Terlambat)**. Mereka tidak memprediksi, mereka hanya 
    **mengkonfirmasi** tren yang *sudah* terjadi.
    
    * **Golden Cross (MA 50 > MA 100):** Mengkonfirmasi tren jangka panjang adalah **Naik (Bullish)**.
    * **Death Cross (MA 50 < MA 100):** Mengkonfirmasi tren jangka panjang adalah **Turun (Bearish)**.
    * **Kekuatan:** Bagus untuk menentukan "gambaran besar" (Konteks).
    * **Kelemahan:** Sangat lambat.
    """)

with st.expander("Pola Harga (Double Top/Bottom) - 'Peta' Gambaran Besar"):
    st.markdown("""
    Ini adalah fondasi dari analisis teknikal. Mereka adalah "Set-Up" atau Peta Anda.
    
    * **Double Bottom (Pola 'W'):** Menunjukkan support kuat. Sinyal potensi berbalik arah NAIK.
    * **Double Top (Pola 'M'):** Menunjukkan resistance kuat. Sinyal potensi berbalik arah TURUN.
    * **Kekuatan:** Memberi Anda gambaran strategis jangka panjang.
    * **Kelemahan:** Membutuhkan konfirmasi dari 'GPS' (Momentum) untuk waktu masuk yang tepat.
    """)
    
# ==========================================================
# BAGIAN 5: PENTINGNYA PERIODE WAKTU
# ==========================================================
st.header("Bagian 5: Pentingnya Periode Waktu (Timeframe)")
with st.expander("Periode '1 Hari' (Intraday) vs '1 Tahun' (Swing)"):
    st.markdown("""
    Periode yang Anda pilih menentukan fokus Anda.
    
    * **Periode '1 Hari' (Interval 1 Menit):** Anda adalah *Day Trader*. Fokus pada **MACD** dan **RSI**.
    * **Periode '1 Tahun' (Interval 1 Hari):** Anda adalah *Swing/Position Trader*. Fokus pada **Pola (DT/DB)** dan **Moving Average (MA)**.
    """)

# ==========================================================
# BAGIAN 6: CARA MEMBACA SCREENER TEKNIKAL
# ==========================================================
st.header("Bagian 6: Cara Membaca Screener Teknikal")
with st.expander("Mode Otomatis: Top 10 Sinyal Emas"):
    st.markdown("""
    Ini adalah fitur premium terkuat. Fitur ini memindai 80 saham IDX80 untuk Anda.
    
    * **Logika Prioritas:**
        1.  Ia akan mencari saham yang memiliki **SINYAL EMAS (Prioritas 1)**: `MACD Cross Up (BUY)` + `Pola Double Bottom (BUY)` secara bersamaan.
        2.  Jika hasilnya kurang dari 10, ia akan mengisi sisanya dengan **Prioritas 2**: saham yang "hanya" mengalami `MACD Cross Up (BUY)`.
    """)

# ==========================================================
# BAGIAN 7: CARA MEMBACA SCREENER FUNDAMENTAL
# ==========================================================
st.header("Bagian 7: Cara Membaca Screener Fundamental")
st.markdown("""
Screener ini membantu Anda mencari saham yang "sehat" atau "murah" secara bisnis. 
Data ini di-cache selama 4 jam (mungkin lambat saat pertama kali dibuka).
""")

with st.expander("Apa itu P/E Ratio (Price-to-Earnings)?"):
    st.markdown("""
    * **Singkatnya:** Harga Saham / Laba per Saham.
    * **Artinya:** Seberapa "mahal" sebuah saham relatif terhadap laba yang dihasilkannya.
    * **Cara Pakai:** Umumnya, **P/E lebih rendah lebih baik** (dianggap "murah").
    """)
    
with st.expander("Apa itu P/B Ratio (Price-to-Book)?"):
    st.markdown("""
    * **Singkatnya:** Harga Saham / Nilai Buku per Saham.
    * **Artinya:** Seberapa "mahal" sebuah saham relatif terhadap *nilai aset bersih* perusahaan.
    * **Cara Pakai:** Umumnya, **P/B lebih rendah lebih baik**.
    """)
    
with st.expander("Apa itu Dividend Yield (Imbal Hasil Dividen)?"):
    st.markdown("""
    * **Singkatnya:** (Dividen per Saham / Harga Saham) * 100%.
    * **Artinya:** "Bunga" yang Anda dapatkan dari saham dalam bentuk dividen.
    * **Cara Pakai:** Umumnya, **Yield lebih tinggi lebih baik**.
    """)

# ==========================================================
# BAGIAN 8: CARA MEMBACA ANALISIS MULTI-TIMEFRAME (MTA)
# ==========================================================
st.header("Bagian 8: Cara Membaca Analisis Multi-Timeframe (MTA)")
st.markdown("""
Panel MTA di halaman utama adalah alat konfirmasi profesional. Ia membandingkan sinyal 
di berbagai jangka waktu untuk satu saham.
""")

with st.expander("Skenario 1: Konfirmasi (Confirmation)"):
    st.markdown("""
    * **Contoh:** Anda melihat sinyal `MACD: 🟢 BUY (Cross Up)` di periode **15 Menit**.
    * **Cek MTA:** Anda melihat panel MTA juga menunjukkan `MACD: 🟢 BUY (Tren Naik)` di **1 Jam** dan **1 Hari**.
    * **Artinya:** Ini adalah **SINYAL BELI KUAT**. Jangka pendek Anda didukung oleh tren jangka panjang.
    """)

with st.expander("Skenario 2: Konflik (Conflict / High-Risk)"):
    st.markdown("""
    * **Contoh:** Anda melihat sinyal `MACD: 🟢 BUY (Cross Up)` di periode **15 Menit**.
    * **Cek MTA:** Anda melihat panel MTA menunjukkan `MACD: 🔴 SELL (Tren Turun)` di **1 Jam** dan **1 Hari**.
    * **Artinya:** Ini adalah **SINYAL BELI BERISIKO TINGGI**. Kenaikan di 15 Menit kemungkinan besar hanyalah *rebound* kecil dalam tren turun yang jauh lebih besar.
    """)

# ==========================================================
# BAGIAN 9: MEMAHAMI PREDIKSI MACHINE LEARNING (ML)
# ==========================================================
st.header("Bagian 9: Memahami Prediksi Machine Learning (ML)")
st.markdown("""
Kartu Prediksi ML adalah fitur eksperimental yang mencoba menebak arah harga "besok" 
(atau periode selanjutnya) berdasarkan pola indikator di masa lalu.
""")

with st.expander("Mengapa Akurasi (Acc: ...%) Selalu Berubah?"):
    st.markdown("""
    Ini adalah fitur *terbaru* (V2.1). Model ML ini **DILATIH SECARA DINAMIS DAN UNIK UNTUK SETIAP SAHAM**.
    
    * **Contoh:**
        * Saat Anda membuka `BBCA.JK`, aplikasi melatih model *khusus* untuk BBCA (misal: Akurasi 62.5%).
        * Saat Anda membuka `GOTO.JK`, aplikasi melatih model *khusus* untuk GOTO (misal: Akurasi 51.2%).
    
    * **Artinya:** Akurasi yang Anda lihat adalah seberapa sering model ML ini **benar** dalam memprediksi saham **spesifik tersebut** di masa lalu. Akurasi > 55% dianggap baik.
    """)

# ==========================================================
# BAGIAN 10: MANAJEMEN ASET (PORTOFOLIO & WATCHLIST)
# ==========================================================
st.header("Bagian 10: Manajemen Aset (Portofolio & Watchlist)")
st.markdown("""
Gunakan fitur di sidebar untuk melacak investasi dan saham yang Anda pantau.
""")

with st.expander("PENTING: Database Permanen (V3.0)"):
    st.markdown("""
    Mulai V3.0, Portofolio dan Watchlist Anda **AMAN**. 
    
    Data Anda disimpan di database cloud pribadi Anda, bukan lagi di cache browser (`st.session_state`). 
    Anda bisa me-refresh halaman, menutup browser, atau membuka dari perangkat lain, dan data Anda akan tetap ada.
    """)

with st.expander("Penting! Sistem Portofolio Menggunakan LOT"):
    st.markdown("""
    Sesuai standar Bursa Efek Indonesia (BEI), semua input di "Portofolio Tracker" (Tambah/Edit Saham) sekarang menggunakan satuan **LOT**.
    
    **1 LOT = 100 LEMBAR SAHAM**
    
    * **Contoh Input:** Jika Anda membeli 5 Lot, masukkan `5` di form "Jumlah Lot". Aplikasi akan otomatis menghitungnya sebagai 500 lembar untuk disimpan di database.
    * **Tampilan:** Semua tampilan di "Detail Saham" juga akan dikonversi dari lembar ke Lot.
    """)

with st.expander("Input Ticker Fleksibel (Tanpa .JK)"):
    st.markdown("""
    Untuk mempercepat input Anda, Anda tidak perlu lagi mengetik `.JK` di akhir.
    
    * **Contoh:** Cukup ketik `BBCA` (atau `bbca`, `Bbca`) di form Analisis, Watchlist, atau Portofolio. Aplikasi akan otomatis mengubahnya menjadi `BBCA.JK`.
    """)

with st.expander("Perbedaan Portofolio vs Watchlist"):
    st.markdown("""
    * **Portofolio:** Untuk saham yang **SUDAH ANDA BELI**. Anda harus memasukkan Harga Beli dan Jumlah Lot agar aplikasi bisa menghitung Untung/Rugi (Profit/Loss).
    * **Watchlist:** Untuk saham yang **SEDANG ANDA PANTAU** (belum dibeli). Aplikasi hanya akan menampilkan "Mini-Dashboard" (Harga, %, RSI, MACD) untuk saham-saham ini.
    """)

