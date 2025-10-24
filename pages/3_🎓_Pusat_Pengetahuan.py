import streamlit as st

# ==========================================================
# KONFIGURASI HALAMAN
# ==========================================================
st.set_page_config(
    page_title="Pusat Pengetahuan",
    layout="wide"
)

st.title("🎓 Pusat Pengetahuan V2.1.1")
st.markdown("---")

# ==========================================================
# BAGIAN 1: CATATAN RILIS (CHANGELOG) - (BARU!)
# ==========================================================
st.header("Bagian 1: Catatan Rilis (Changelog)")
st.markdown("Lihat apa saja yang baru di Pro Stock Analyzer!")

with st.expander("Versi 2.1.1 (14 Okt 2025) - Input Polish"):
    st.markdown("""
    - **Input Ticker Fleksibel:** Anda sekarang bisa mengetik `BBCA`, `bbca`, atau `Bbca` di semua form input (Analisis, Watchlist, Portofolio). Aplikasi akan otomatis mengubahnya menjadi `BBCA.JK`.
    - **Sistem Portofolio per LOT:** Semua input di Portofolio Tracker (Tambah/Edit) sekarang menggunakan **LOT** (1 Lot = 100 Lembar), bukan lagi lembar. Tampilan juga disesuaikan untuk menunjukkan Lot.
    - **Perbaikan Bug Kritis:** Memperbaiki `KeyError` di Tab Watchlist yang bisa terjadi jika ticker yang error ditambahkan.
    """)

with st.expander("Versi 2.1.0 (13 Okt 2025) - Mobile Polish"):
    st.markdown("""
    - **UI Mobile-Friendly:** Merombak total tampilan di halaman utama (`app.py`).
    - **"Result Cards":** Menghapus semua `st.dataframe` yang tidak ramah HP (di tab MTA, Watchlist, Portofolio) dan menggantinya dengan "Kartu Hasil" yang rapi dan *responsive*.
    - **Ringkasan Ramping:** Mengubah 5 kartu ringkasan menjadi 3 kartu utama + `st.expander` "Info Tambahan" untuk menghemat ruang di HP.
    - **Grafik Interaktif (Sentuh):** Meng-upgrade semua grafik (`plotter.py`) agar *default* ke mode "Pan" (Geser), mendukung "Pinch-to-Zoom" (Cubit), dan menampilkan detail saat disentuh (`hover`).
    - **Perbaikan Bug ML Dinamis:** Memperbaiki bug "Akurasi 47.8%" yang selalu sama. Model ML sekarang dilatih secara dinamis *per-saham* dan akurasinya unik untuk setiap saham.
    """)

with st.expander("Versi 2.0.0 (12 Okt 2025) - Fitur Fundamental"):
    st.markdown("""
    - **Screener Fundamental:** Menambahkan Tab "Screener Fundamental" baru di halaman Screener. Pengguna sekarang bisa memindai 80 saham IDX80 berdasarkan P/E Ratio, P/B Ratio, dan Dividend Yield.
    - **Arsitektur Screener:** Mengubah halaman Screener dari "Mode" menjadi "Tabs" (Teknikal & Fundamental).
    """)

with st.expander("Versi 1.2.0 (11 Okt 2025) - Fitur MTA"):
    st.markdown("""
    - **Analisis Multi-Timeframe (MTA):** Menambahkan panel MTA baru di halaman utama. Panel ini otomatis memindai saham di 4 periode (15m, 1h, 1d, 1wk) dan menampilkan status RSI & MACD dalam satu tabel.
    """)
    
with st.expander("Versi 1.1.0 (10 Okt 2025) - Fitur Watchlist"):
    st.markdown("""
    - **Watchlist & Mini-Dashboard:** Menambahkan Tab "Watchlist Saya" baru di halaman utama. Pengguna bisa menambah/menghapus saham, dan Tab ini akan menampilkan "Mini-Dashboard" (Harga, %, RSI, MACD) untuk semua saham yang dipantau.
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
    * **Cara Membaca:** Sinyal Beli dari MACD ini adalah *palsu*. Ini adalah reli terakhir yang memancing pembeli baru masuk tepat sebelum harga berbalik arah turun. Trader pro akan mengabaikan sinyal Beli MACD dan menunggu MACD berbalik menjadi "SELL" sebagai konfirmasi untuk ikut menjual.
    """)

with st.expander("Studi Kasus 2: Pola Double Bottom (BUY) 🟢 vs MACD (SELL) 🔴"):
    st.markdown("""
    Ini adalah skenario paling umum saat menunggu konfirmasi.
    
    * **Apa yang Terjadi?** Harga *baru saja jatuh* untuk membentuk "Lembah ke-2" (bagian akhir dari huruf 'W'). Karena harga baru saja jatuh, wajar jika MACD (GPS) masih memberi sinyal "SELL".
    * **Pola (Peta) Berkata:** "Area support kuat! Bersiap Beli!"
    * **Momentum (GPS) Berkata:** "Jual! Momentum masih negatif!"
    * **Rekomendasi:** **TUNGGU KONFIRMASI (JANGAN BELI DULU).** ⚠️
    * **Cara Membaca:** Peta Anda sudah benar, tapi GPS Anda belum siap. Jika Anda beli sekarang, harga bisa turun sedikit lagi. Trader pro akan **menunggu** sampai MACD juga *cross up* (memberi sinyal BUY). Itulah konfirmasi Anda untuk masuk.
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
    
    * **MACD:** Mengukur momentum Beli vs Jual. Sinyal utamanya adalah "Cross" (persilangan).
    * **RSI & Stochastic:** Mengukur kejenuhan pasar. Apakah harga sudah "terlalu mahal" (Overbought) atau "terlalu murah" (Oversold)?
    * **Kekuatan:** Sangat cepat memberi sinyal.
    * **Kelemahan:** Sering memberi sinyal palsu (seperti pada *Bull Trap*).
    """)

with st.expander("Indikator Tren (Moving Average/MA) - 'Konteks' Jangka Panjang"):
    st.markdown("""
    Indikator ini adalah **Lagging (Terlambat)**. Mereka tidak memprediksi, mereka hanya 
    **mengkonfirmasi** tren yang *sudah* terjadi dengan merata-ratakan harga.
    
    * **Golden Cross (MA 50 > MA 100):** Mengkonfirmasi bahwa tren jangka panjang adalah **Naik (Bullish)**.
    * **Death Cross (MA 50 < MA 100):** Mengkonfirmasi bahwa tren jangka panjang adalah **Turun (Bearish)**.
    * **Kekuatan:** Sangat bagus untuk menentukan "gambaran besar" (Konteks).
    * **Kelemahan:** Sangat lambat. Saat Golden Cross terjadi, harga mungkin sudah naik banyak.
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
    Logika Anda sudah tepat: **Periode yang Anda pilih menentukan fokus Anda.**
    
    * **Periode '1 Hari' (Interval 1 Menit):** Anda adalah *Day Trader*. Anda fokus pada sinyal jangka pendek (beli pagi jual sore). Di sini, **MACD** dan **RSI** adalah raja Anda.
    * **Mengapa Pola (DT/DB) Muncul di '1 Hari'?** Berkat *upgrade* V1.0, aplikasi ini sekarang "pintar". Ia mencari **Pola Intraday** (pola 'M' atau 'W' kecil yang terbentuk dalam beberapa jam). Jadi, jika Anda melihat Double Bottom dan MACD Buy di periode 1-menit, itu adalah sinyal *day trading* yang sangat kuat.
    * **Periode '1 Tahun' (Interval 1 Hari):** Anda adalah *Swing/Position Trader*. Anda fokus pada gambaran besar. Di sini, **Pola (DT/DB)** dan **Moving Average (MA)** adalah raja Anda.
    """)

# ==========================================================
# BAGIAN 6: CARA MEMBACA SCREENER TEKNIKAL (BARU!)
# ==========================================================
st.header("Bagian 6: Cara Membaca Screener Teknikal")
with st.expander("Mode Otomatis: Top 10 Sinyal Emas"):
    st.markdown("""
    Ini adalah fitur premium terkuat. Fitur ini memindai 80 saham IDX80 untuk Anda.
    
    * **Logika Prioritas:**
        1.  Ia akan mencari saham yang memiliki **SINYAL EMAS (Prioritas 1)**: yaitu saham yang **BARU SAJA** mengalami `MACD Cross Up (BUY)` DAN `Pola Double Bottom (BUY)` secara bersamaan di periode yang Anda pilih.
        2.  Jika hasilnya kurang dari 10 (misal: hanya ada 4), ia akan mengisi 6 slot sisanya dengan **Prioritas 2**: saham yang "hanya" mengalami `MACD Cross Up (BUY)`.
    * **Periode:** Anda bisa menjalankan pindaian ini di semua periode. Menjalankannya di "1 Hari (Intraday)" akan memberi Anda sinyal untuk *day trading*, sementara menjalankannya di "1 Tahun (Swing)" akan memberi Anda sinyal untuk *swing trading*.
    """)

# ==========================================================
# BAGIAN 7: CARA MEMBACA SCREENER FUNDAMENTAL (BARU!)
# ==========================================================
st.header("Bagian 7: Cara Membaca Screener Fundamental")
st.markdown("""
Screener ini membantu Anda mencari saham yang "sehat" atau "murah" secara bisnis, 
bukan hanya dari grafik. Ini menggunakan data yang di-cache selama 4 jam (jadi mungkin lambat saat pertama kali dibuka).
""")

with st.expander("Apa itu P/E Ratio (Price-to-Earnings)?"):
    st.markdown("""
    * **Singkatnya:** Harga Saham / Laba per Saham.
    * **Artinya:** Seberapa "mahal" sebuah saham relatif terhadap laba yang dihasilkannya. P/E 15x berarti Anda membayar Rp 15 untuk setiap Rp 1 laba perusahaan.
    * **Cara Pakai:** Umumnya, **P/E lebih rendah lebih baik** (dianggap "murah"). Memfilter P/E < 25 adalah awal yang baik. Hindari P/E negatif (artinya perusahaan rugi).
    """)
    
with st.expander("Apa itu P/B Ratio (Price-to-Book)?"):
    st.markdown("""
    * **Singkatnya:** Harga Saham / Nilai Buku per Saham.
    * **Artinya:** Seberapa "mahal" sebuah saham relatif terhadap *nilai aset bersih* perusahaan. P/B 2x berarti Anda membayar Rp 2 untuk setiap Rp 1 aset bersih yang dimiliki perusahaan.
    * **Cara Pakai:** Umumnya, **P/B lebih rendah lebih baik**. P/B < 3 sering dianggap wajar.
    """)
    
with st.expander("Apa itu Dividend Yield (Imbal Hasil Dividen)?"):
    st.markdown("""
    * **Singkatnya:** (Dividen per Saham / Harga Saham) * 100%.
    * **Artinya:** "Bunga" yang Anda dapatkan dari saham dalam bentuk dividen.
    * **Cara Pakai:** Umumnya, **Yield lebih tinggi lebih baik**. Jika Anda investor jangka panjang yang mencari pendapatan pasif, carilah saham dengan Div. Yield > 2% (idealnya di atas bunga deposito).
    """)

# ==========================================================
# BAGIAN 8: CARA MEMBACA ANALISIS MULTI-TIMEFRAME (MTA) (BARU!)
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
    * **Artinya:** Ini adalah **SINYAL BELI KUAT**. Jangka pendek Anda (15m) didukung oleh tren jangka menengah (1h) dan panjang (1d).
    """)

with st.expander("Skenario 2: Konflik (Conflict / High-Risk)"):
    st.markdown("""
    * **Contoh:** Anda melihat sinyal `MACD: 🟢 BUY (Cross Up)` di periode **15 Menit**.
    * **Cek MTA:** Anda melihat panel MTA menunjukkan `MACD: 🔴 SELL (Tren Turun)` di **1 Jam** dan **1 Hari**.
    * **Artinya:** Ini adalah **SINYAL BELI BERISIKO TINGGI**. Kenaikan di 15 Menit kemungkinan besar hanyalah *rebound* kecil dalam tren turun yang jauh lebih besar. Ini adalah *jebakan* (Bull Trap).
    """)

# ==========================================================
# BAGIAN 9: MEMAHAMI PREDIKSI MACHINE LEARNING (ML) (BARU!)
# ==========================================================
st.header("Bagian 9: Memahami Prediksi Machine Learning (ML)")
st.markdown("""
Kartu Prediksi ML adalah fitur eksperimental yang mencoba menebak arah harga "besok" 
(atau periode selanjutnya) berdasarkan pola indikator di masa lalu.
""")

with st.expander("Mengapa Akurasi (Acc: ...%) Selalu Berubah?"):
    st.markdown("""
    Ini adalah fitur *terbaru* (V2.1). Berbeda dari sebelumnya, model ML ini **DILATIH SECARA DINAMIS DAN UNIK UNTUK SETIAP SAHAM**.
    
    * **Contoh:**
        * Saat Anda membuka `BBCA.JK`, aplikasi melatih model *khusus* untuk BBCA (misal: Akurasi 62.5%).
        * Saat Anda membuka `GOTO.JK`, aplikasi melatih model *khusus* untuk GOTO (misal: Akurasi 51.2%).
    
    * **Artinya:** Akurasi yang Anda lihat adalah seberapa sering model ML ini **benar** dalam memprediksi saham **spesifik tersebut** di masa lalu (berdasarkan data 20% terakhir). Akurasi > 55% dianggap baik.
    """)

# ==========================================================
# BAGIAN 10: MANAJEMEN ASET (PORTOFOLIO & WATCHLIST) (BARU!)
# ==========================================================
st.header("Bagian 10: Manajemen Aset (Portofolio & Watchlist)")
st.markdown("""
Gunakan fitur di sidebar untuk melacak investasi dan saham yang Anda pantau.
""")

with st.expander("Penting! Sistem Portofolio Menggunakan LOT"):
    st.markdown("""
    Sesuai standar Bursa Efek Indonesia (BEI), semua input di "Portofolio Tracker" (Tambah/Edit Saham) sekarang menggunakan satuan **LOT**.
    
    **1 LOT = 100 LEMBAR SAHAM**
    
    * **Contoh Input:** Jika Anda membeli 5 Lot, masukkan `5` di form "Jumlah Lot". Aplikasi akan otomatis menghitungnya sebagai 500 lembar.
    * **Tampilan:** Semua tampilan di "Detail Saham" juga akan dikonversi ke Lot.
    """)

with st.expander("Input Ticker Fleksibel (Tanpa .JK)"):
    st.markdown("""
    Untuk mempercepat input Anda, Anda tidak perlu lagi mengetik `.JK` di akhir.
    
    * **Contoh:** Cukup ketik `BBCA` (atau `bbca`, `Bbca`) di form Analisis, Watchlist, atau Portofolio. Aplikasi akan otomatis mengubahnya menjadi `BBCA.JK`.
    """)

with st.expander("Perbedaan Portofolio vs Watchlist"):
    st.markdown("""
    * **Portofolio:** Untuk saham yang **SUDAH ANDA BELI**. Anda harus memasukkan Harga Beli dan Jumlah Lot agar aplikasi bisa menghitung Untung/Rugi (Profit/Loss).
    * **Watchlist:** Untuk saham yang **SEDANG ANDA PANTAU** (belum dibeli). Aplikasi hanya akan menampilkan "Mini-Dashboard" (Harga, %, RSI, MACD) untuk saham-saham ini agar Anda bisa memantaunya dengan cepat.
    """)

