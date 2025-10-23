#!/bin/bash

# Opsional: Ganti 'venv' dengan nama virtual environment Anda jika ada
# Jika Anda menggunakan virtual environment:
source venv_stable/bin/activate

# Jalankan aplikasi Python Anda
streamlit run app.py

# Opsional: Menjaga jendela Terminal tetap terbuka setelah eksekusi selesai
echo "========================================="
echo "Program selesai. Tekan Enter untuk keluar..."
read