# pages/3_🎓_Pusat_Pengetahuan.py (V9.x - Sesuai Versi Terbaru - LENGKAP)

import streamlit as st

# ==========================================================
# KONFIGURASI HALAMAN
# ==========================================================
st.set_page_config(
    page_title="Pusat Pengetahuan",
    page_icon="🎓", # Menambahkan ikon
    layout="wide"
)

# --- PERBARUI JUDUL & VERSI ---
st.title("🎓 Pusat Pengetahuan")
st.markdown("---")

# ==========================================================
# BAGIAN 1: CATATAN RILIS (CHANGELOG) - (DIPERBARUI!)
# ==========================================================
st.header("Bagian 1: Catatan Rilis (Changelog)")
st.markdown("Lihat apa saja yang baru di Pro Stock Analyzer!")

# --- PERBARUI VERSI INI ---
with st.expander("Versi 4.0.0 (27 Okt 2025) - Rekomendasi Premium & Database Excel (BARU!)"):
    st.markdown("""
    - **FITUR PREMIUM: Rekomendasi Beli & Jual!**
        - Menambahkan halaman baru **'4_🎯_Rekomendasi_Premium'**.
        - **Rekomendasi Beli:** Analisis 1 ticker untuk potensi beli jangka pendek, lengkap dengan area beli, target profit (TP), stop loss (SL), analisis Risk/Reward (kualitatif & per lembar), dan penjelasan detail berdasarkan ML, Prophet, & TA. Fokus pada sinyal beli **1-5 hari**.
        - **Rekomendasi Jual:** Memindahkan fitur rekomendasi jual dari halaman utama. Memberikan saran jual yang mempertimbangkan harga beli Anda, status P/L saat ini, prediksi ML & Prophet, serta level resistance. Rekomendasi harga **dibulatkan** agar stabil dan penjelasan **lebih detail**.
    - **Penyempurnaan Screener Beli:**
        - Halaman `2_📈_Screener.py` kini fokus mencari sinyal beli terbaik ("Ide B").
        - Menghapus mode manual teknikal.
        - Menggunakan sistem **skoring** berdasarkan kekuatan sinyal MACD (Cross Up?), RSI (Keluar Oversold? Netral?), dan Volume (Naik?).
        - Menampilkan hasil yang diurutkan berdasarkan skor dengan tampilan yang lebih informatif.
    - **Perbaikan Bug & Stabilitas:**
        - Memperbaiki bug `cache` yang menyebabkan rekomendasi jual selalu sama.
        - Memperbaiki `NameError` dan `Positional argument` error terkait `st.metric` dan `st.form`.
        - Memperbaiki bug `NameError: prophet_model`.
        - Memperbaiki bug tampilan `DeltaGenerator`.
        - Memperbaiki `NameError: selected_wl_ticker`.
    - **Refactor Kode:** Memindahkan logika rekomendasi ke halaman terpisah. Meningkatkan kejelasan logika R/R.
    """)

# --- PERBARUI VERSI INI ---
with st.expander("Versi 3.0.0 (Revisi - 27 Okt 2025) - Database Lokal (Excel)"):
    st.markdown("""
    - **DATABASE LOKAL (EXCEL)!** Perubahan arsitektur signifikan.
    - **Data Tersimpan Lokal:** Portofolio dan Watchlist Anda sekarang disimpan di file **`portfolio_data.xlsx`** dan **`watchlist_data.xlsx`** di komputer Anda.
    - **Otomatis Load/Save:** Aplikasi akan otomatis memuat data saat dimulai dan menyimpan perubahan saat Anda menambah/mengedit/menghapus item.
    - **Menghapus Ketergantungan Cloud:** Tidak lagi memerlukan koneksi database Supabase atau `st.connection`. Lebih mudah di-deploy.
    - **Perbaikan Performa:** Mengoptimalkan loading data Excel dan pengambilan harga terkini menggunakan cache yang benar.
    - **Perbaikan Bug:** Menyelesaikan berbagai `ImportError`, bug `cache`, `KeyError` `session_state`, dan bug tampilan `DeltaGenerator`.
    - **Struktur Kode:** Menggunakan pola inisialisasi `session_state` yang aman di `__init__` class Tracker.
    - **Keamanan:** Memindahkan kunci API (Telegram) ke `st.secrets`.
    - **Dependensi:** Membersihkan `requirements.txt`, menghapus `TA-Lib`, `psycopg2`, `firebase-admin`, dan memastikan semua dependensi `prophet` ada.
    """)

# Changelog versi sebelumnya
with st.expander("Versi 2.1.1 (14 Okt 2025) - Input Polish"):
    st.markdown("""
    - **Input Ticker Fleksibel:** Bisa ketik `BBCA` atau `bbca` (tanpa `.JK`).
    - **Sistem Portofolio per LOT:** Input di Portofolio Tracker menggunakan **LOT**.
    - **Perbaikan Bug Kritis:** Memperbaiki `KeyError` di Tab Watchlist (versi lama).
    """)

with st.expander("Versi 2.1.0 (13 Okt 2025) - Mobile Polish"):
    st.markdown("""
    - **UI Mobile-Friendly:** Merombak tampilan halaman utama (Kartu Hasil, Grafik Interaktif).
    - **Perbaikan Bug ML Dinamis:** Memperbaiki akurasi ML yang selalu sama (versi lama).
    """)

with st.expander("Versi 2.0.0 (12 Okt 2025) - Fitur Fundamental"):
    st.markdown("""
    - **Screener Fundamental:** Menambahkan Tab Screener Fundamental (P/E, P/B, Dividen).
    """)

with st.expander("Versi 1.0.0 - 1.2.0 (Rilis Awal)"):
     st.markdown("""
    - Fitur Inti: Analisis Utama (Grafik, Indikator, Backtesting), MTA, Watchlist, Screener Teknikal awal, Portofolio awal.
    """)

# ==========================================================
# BAGIAN 2: KONFLIK SINYAL
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
    * **Cara Membaca:** Sinyal Beli dari MACD ini adalah *palsu*. Ini adalah reli terakhir yang memancing pembeli baru masuk tepat sebelum harga berbalik arah turun.
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
with st.expander("Sinyal Beli Kuat: MACD Positif 🟢 + RSI Tidak Overbought 👍 (+ Volume Naik ✅)"):
    st.markdown("""
    Inilah kombinasi yang dicari oleh fitur **"Pencari Sinyal Beli Terbaik"** di halaman Screener.

    * **Momentum (GPS):** MACD sudah *cross up* atau sedang tren naik.
    * **Kondisi Harga:** RSI netral atau baru keluar dari *oversold*, menunjukkan harga belum jenuh beli.
    * **Konfirmasi Volume (Opsional tapi bagus):** Volume transaksi di atas rata-rata menunjukkan minat beli yang kuat.
    * **Cara Membaca:** Ini adalah sinyal beli jangka pendek dengan probabilitas yang baik. Semakin tinggi skor di Screener, semakin kuat kombinasinya.
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

    * **Golden Cross (MA Pendek > MA Panjang):** Mengkonfirmasi tren jangka panjang adalah **Naik (Bullish)**.
    * **Death Cross (MA Pendek < MA Panjang):** Mengkonfirmasi tren jangka panjang adalah **Turun (Bearish)**.
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
with st.expander("Periode Data di Analisis Utama vs Screener vs Rekomendasi"):
    st.markdown("""
    Periode yang Anda pilih memengaruhi sinyal yang dihasilkan:

    * **Analisis Utama (Halaman 1):** Anda bisa memilih periode sangat pendek (misal '1 Hari' / 1 Menit) hingga sangat panjang ('Maksimal' / 1 Minggu). Sesuaikan dengan gaya trading Anda (Day Trader vs Investor).
    * **Screener Sinyal Beli (Halaman 2):** Fokus pada periode jangka pendek hingga menengah ('1 Minggu' hingga '1 Tahun') karena tujuannya mencari sinyal beli untuk beberapa hari/minggu ke depan.
    * **Rekomendasi Premium (Halaman 4):** Menggunakan data '1 Tahun' (harian) sebagai dasar analisis ML, Prophet, dan TA untuk memberikan rekomendasi jangka pendek/menengah (beli 1-5 hari, jual 1-2 minggu).
    """)

# ==========================================================
# BAGIAN 6: CARA MEMBACA SCREENER SINYAL BELI
# ==========================================================
st.header("Bagian 6: Cara Membaca Screener Sinyal Beli")
with st.expander("Memahami Hasil Pencarian Sinyal Beli Terbaik"):
    st.markdown("""
    Fitur ini (di halaman 'Screener Saham') memindai saham IDX80 untuk mencari kombinasi sinyal beli jangka pendek yang kuat.

    * **Logika Inti:**
        1.  Saham **harus** memenuhi: MACD di atas *signal line* (tren naik) **DAN** RSI tidak *Overbought* (harga belum jenuh beli).
        2.  Saham yang lolos kemudian diberi **Skor** berdasarkan bonus:
            * MACD baru *cross up* (+3)
            * RSI baru keluar *Oversold* (+3) / RSI Netral Bawah (+2) / RSI Netral Atas (+1)
            * Volume di atas rata-rata (+2)
    * **Cara Membaca Tabel Hasil:**
        - Saham diurutkan dari **Skor tertinggi** (paling potensial).
        - Perhatikan kolom **RSI** dan **MACD** untuk melihat detail sinyal.
        - Kolom **Volume** ('Naik ✅' / 'Normal ➖') menunjukkan konfirmasi minat pasar.
        - Gunakan hasil ini sebagai **titik awal riset**, bukan rekomendasi beli langsung. Selalu cek grafik dan analisis lebih lanjut di halaman utama atau rekomendasi premium.
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
    * **Cara Pakai:** Umumnya, **P/E lebih rendah lebih baik** (dianggap "murah"). Bandingkan dengan rata-rata industri atau historis saham itu sendiri.
    """)

with st.expander("Apa itu P/B Ratio (Price-to-Book)?"):
    st.markdown("""
    * **Singkatnya:** Harga Saham / Nilai Buku per Saham.
    * **Artinya:** Seberapa "mahal" sebuah saham relatif terhadap *nilai aset bersih* perusahaan jika dilikuidasi.
    * **Cara Pakai:** Umumnya, **P/B lebih rendah lebih baik**. P/B < 1 sering dianggap murah. Berguna untuk sektor seperti perbankan atau properti.
    """)

with st.expander("Apa itu Dividend Yield (Imbal Hasil Dividen)?"):
    st.markdown("""
    * **Singkatnya:** (Dividen Tahunan per Saham / Harga Saham) * 100%.
    * **Artinya:** "Bunga" atau imbal hasil pasif yang Anda dapatkan dari saham dalam bentuk dividen.
    * **Cara Pakai:** Umumnya, **Yield lebih tinggi lebih menarik**, terutama untuk investor jangka panjang yang mencari pendapatan pasif. Pastikan juga perusahaan mampu membayar dividen secara konsisten.
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
    * **Artinya:** Ini adalah **SINYAL BELI KUAT**. Sinyal jangka pendek Anda didukung oleh tren jangka menengah dan panjang.
    """)

with st.expander("Skenario 2: Konflik (Conflict / High-Risk)"):
    st.markdown("""
    * **Contoh:** Anda melihat sinyal `MACD: 🟢 BUY (Cross Up)` di periode **15 Menit**.
    * **Cek MTA:** Anda melihat panel MTA menunjukkan `MACD: 🔴 SELL (Tren Turun)` di **1 Jam** dan **1 Hari**.
    * **Artinya:** Ini adalah **SINYAL BELI BERISIKO TINGGI**. Kenaikan di 15 Menit kemungkinan besar hanyalah *rebound* teknikal (kenaikan sementara) dalam tren turun jangka panjang yang lebih besar. Hati-hati 'terjebak'.
    """)

# ==========================================================
# BAGIAN 9: MEMAHAMI PREDIKSI MACHINE LEARNING (ML)
# ==========================================================
st.header("Bagian 9: Memahami Prediksi Machine Learning (ML)")
st.markdown("""
Kartu Prediksi ML di halaman utama dan nilai Akurasi di Rekomendasi Premium adalah fitur yang mencoba menebak **arah** harga selanjutnya (naik/turun) berdasarkan pola indikator di masa lalu untuk saham **spesifik** tersebut.
""")

with st.expander("Mengapa Akurasi (Acc: ...%) Selalu Berubah?"):
    st.markdown("""
    Model ML ini **DILATIH SECARA DINAMIS DAN UNIK UNTUK SETIAP SAHAM** saat Anda menganalisisnya.

    * **Contoh:**
        * Saat Anda menganalisis `BBCA.JK`, aplikasi melatih model *khusus* untuk BBCA menggunakan data historisnya (misal: Akurasi 62.5%).
        * Saat Anda menganalisis `GOTO.JK`, aplikasi melatih model *khusus* untuk GOTO (misal: Akurasi 51.2%).

    * **Artinya:** Akurasi yang Anda lihat adalah seberapa sering model ML ini **benar** dalam memprediksi arah saham **spesifik tersebut** di masa lalu (berdasarkan data *testing*). Akurasi > 55% dianggap cukup baik, namun **bukan jaminan** prediksi masa depan akan benar. Gunakan sebagai salah satu **konfirmasi**, bukan satu-satunya dasar keputusan.
    """)

# ==========================================================
# BAGIAN 10: MANAJEMEN ASET (PORTOFOLIO & WATCHLIST)
# ==========================================================
st.header("Bagian 10: Manajemen Aset (Portofolio & Watchlist)")
st.markdown("""
Gunakan fitur di sidebar untuk melacak investasi dan saham yang Anda pantau.
""")

with st.expander("PENTING: Database Lokal (Excel)"):
    st.markdown("""
    Portofolio dan Watchlist Anda **AMAN di komputer Anda**.

    Data disimpan dalam file **`portfolio_data.xlsx`** dan **`watchlist_data.xlsx`**. Aplikasi akan otomatis memuat file ini saat dibuka dan menyimpan setiap perubahan yang Anda buat (tambah/edit/hapus).

    **Keuntungan:**
    * **Privasi:** Data Anda hanya ada di komputer Anda.
    * **Offline:** Bisa berfungsi tanpa koneksi internet (setelah data saham awal dimuat).
    * **Mudah Backup:** Anda bisa menyalin file Excel ini sebagai cadangan.

    **Kekurangan:**
    * **Tidak Sinkron:** Data tidak tersinkronisasi antar perangkat. Portofolio di laptop berbeda dengan di PC.
    * **Perlu File:** Pastikan file Excel tidak terhapus atau rusak. Jika file rusak/hilang, data Anda juga hilang (kecuali Anda punya backup).
    """)

with st.expander("Penting! Sistem Portofolio Menggunakan LOT"):
    st.markdown("""
    Sesuai standar Bursa Efek Indonesia (BEI), semua input di "Portofolio Tracker" (Tambah/Edit Saham) sekarang menggunakan satuan **LOT**.

    **1 LOT = 100 LEMBAR SAHAM**

    * **Contoh Input:** Jika Anda membeli 5 Lot, masukkan `5` di form "Jumlah Lot". Aplikasi akan otomatis menghitungnya sebagai 500 lembar.
    * **Tampilan:** Semua tampilan di "Detail Saham" juga akan dikonversi dari lembar ke Lot.
    """)

with st.expander("Input Ticker Fleksibel (Tanpa .JK)"):
    st.markdown("""
    Untuk mempercepat input Anda, Anda tidak perlu lagi mengetik `.JK` di akhir.

    * **Contoh:** Cukup ketik `BBCA` (atau `bbca`, `Bbca`) di form Analisis, Watchlist, Portofolio, atau Rekomendasi. Aplikasi akan otomatis mengubahnya menjadi `BBCA.JK`.
    """)

with st.expander("Perbedaan Portofolio vs Watchlist"):
    st.markdown("""
    * **Portofolio:** Untuk saham yang **SUDAH ANDA BELI**. Anda harus memasukkan Harga Beli dan Jumlah Lot agar aplikasi bisa menghitung Untung/Rugi (Profit/Loss).
    * **Watchlist:** Untuk saham yang **SEDANG ANDA PANTAU** (belum dibeli). Aplikasi hanya akan menampilkan "Mini-Dashboard" (Harga, %, RSI, MACD) untuk saham-saham ini di halaman utama.
    """)

# ==========================================================
# BAGIAN 11: FITUR PREMIUM BARU - REKOMENDASI BELI/JUAL
# ==========================================================
st.header("Bagian 11: Fitur Premium - Rekomendasi Beli & Jual")
st.markdown("""
Halaman **'4_🎯_Rekomendasi_Premium'** dirancang untuk memberikan analisis lebih mendalam bagi trader aktif.
""")

with st.expander("Bagaimana Rekomendasi Beli Dihasilkan?"):
     st.markdown("""
     Fitur ini menganalisis satu saham pilihan Anda untuk potensi beli **jangka pendek (1-5 hari)**.
     * **Kriteria Utama:** Mencari kombinasi sinyal positif seperti prediksi ML Naik, MACD baru *cross up* atau tren naik, dan RSI yang tidak *Overbought* (idealnya baru keluar *Oversold* atau netral).
     * **Output:**
         * **Rekomendasi:** Beli / Tunggu Koreksi / Jangan Beli.
         * **Area Beli:** Estimasi harga beli ideal saat ini (dibulatkan).
         * **Target Profit (TP):** Estimasi harga jual untuk profit, berdasarkan *resistance* terdekat atau prediksi Prophet (dibulatkan).
         * **Stop Loss (SL):** Estimasi harga jual untuk membatasi kerugian, berdasarkan *support* terdekat (dibulatkan).
         * **Risk/Reward:** Perbandingan potensi profit vs potensi risiko per lembar, disajikan secara kualitatif (Baik ✅ / Cukup Baik ☑️ / Kurang Ideal ⚠️ / Tidak Valid ❌).
         * **Penjelasan Detail:** Alasan di balik rekomendasi, kondisi indikator, dan estimasi waktu.
     * **Penting:** Ini adalah analisis probabilistik, **bukan jaminan profit**. Selalu lakukan riset Anda sendiri (DYOR) dan **gunakan stop loss** yang direkomendasikan atau sesuai toleransi risiko Anda.
     """)

with st.expander("Bagaimana Rekomendasi Jual Dihasilkan?"):
     st.markdown("""
     Fitur ini menganalisis **posisi saham yang sudah Anda miliki** untuk menentukan waktu jual yang potensial.
     * **Input:** Anda memasukkan Simbol, Harga Beli, dan Jumlah Lot.
     * **Logika Inti:** Mempertimbangkan status Profit/Loss Anda saat ini, prediksi arah jangka pendek (ML), target teknikal (*resistance* atau prediksi Prophet), dan kondisi indikator (RSI/MACD).
     * **Tujuan:** Memberikan rekomendasi harga jual yang **logis** dan **konsisten** (dibulatkan), bertujuan untuk:
         * Mengunci profit jika prediksi cenderung turun atau sudah dekat target.
         * Membatasi kerugian jika prediksi cenderung turun dan posisi sedang rugi.
         * Menentukan target profit realistis jika prediksi cenderung naik (minimal 1% di atas harga beli).
     * **Output:**
         * **Rekomendasi Harga Jual:** Harga spesifik (dibulatkan) atau "Tahan / Pantau".
         * **Estimasi P/L:** Perkiraan untung/rugi jika dijual di harga rekomendasi.
         * **Penjelasan Detail:** Alasan lengkap, termasuk status P/L Anda saat ini dan hasil estimasi jika rekomendasi diikuti.
     * **Penting:** Harga rekomendasi adalah **target**, bukan harga pasti. Pasar bisa berbalik arah sebelum target tercapai. Pertimbangkan untuk menggunakan *trailing stop* jika Anda sudah profit signifikan untuk mengamankan keuntungan.
     """)

st.caption("© 2025 Dibuat oleh Hendrawan Lotanto.")