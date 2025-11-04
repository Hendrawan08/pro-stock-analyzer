import streamlit as st
import os

def check_password(page_name: str, password_env_key: str = "ADMIN_PASSWORD", default_password: str = "hendra08") -> bool:
    """
    Fungsi login universal untuk setiap halaman Streamlit.

    Args:
        page_name (str): nama unik halaman (misal "screener", "developer").
        password_env_key (str): nama variabel environment untuk password.
        default_password (str): password default jika environment tidak tersedia.

    Cara pakai:
        from utils.auth import check_password
        check_password("screener")
    """
    key = f"password_correct_{page_name}"

    if key not in st.session_state:
        st.session_state[key] = False

    # Ambil password dari secrets atau environment
    ADMIN_PASSWORD = None
    try:
        ADMIN_PASSWORD = st.secrets[password_env_key]
    except Exception:
        ADMIN_PASSWORD = os.environ.get(password_env_key, default_password)

    # Jika belum login
    if not st.session_state[key]:
        with st.form(f"login_form_{page_name}"):
            st.title("🔒 Halaman Admin Terproteksi")
            st.write("Halaman ini hanya untuk pemilik aplikasi. Silakan masukkan password untuk melanjutkan.")
            password = st.text_input(f"Masukkan password untuk {page_name.title()}", type="password")
            submit = st.form_submit_button("Login")

        if submit:
            if password == ADMIN_PASSWORD:
                st.session_state[key] = True
                st.success("Login berhasil ✅")
                st.rerun()
            else:
                st.error("Password salah ❌")
                st.stop()
    else:
        return True
