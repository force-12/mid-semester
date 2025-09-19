import streamlit as st
from db2 import get_connection, get_user_role
from admin_dashboard import show_admin_dashboard
from user_dashboard import show_user_dashboard
from daftar import show_register

st.set_page_config(page_title="Halaman Login", page_icon="🔐")

# Inisialisasi session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

def login_page():
    st.title("Halaman Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Masuk"):
        conn = get_connection()
        if conn is None:
            st.error("Gagal koneksi ke database!")
        elif not username or not password:
            st.error("Username dan Password tidak boleh kosong.")
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = get_user_role(username)
                st.rerun()
            else:
                st.error("Username atau Password salah.")

    if st.button("Daftar jika belum ada akun"):
        st.session_state.page = "register"
        st.rerun()

# Router
if st.session_state.logged_in:
    if st.session_state.role == "admin":
        show_admin_dashboard()
    elif st.session_state.role == "user":
        show_user_dashboard()
    else:
        st.error("Peran pengguna tidak dikenal. Silakan hubungi admin.")
        st.session_state.logged_in = False
        st.rerun()
elif st.session_state.page == "register":
    show_register()
else:
    login_page()
    