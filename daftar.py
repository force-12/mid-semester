import streamlit as st
from db2 import get_connection, get_user_role, create_user

def show_register():
    st.title("Halaman Pendaftaran")
    st.write("Silakan buat akun pengguna baru.")

    new_user = st.text_input("Buat Username")
    new_pass = st.text_input("Buat Password", type="password")

    if st.button("Daftar"):
        conn = get_connection()
        if conn is None:
            st.error("Gagal koneksi ke database!")
        elif new_user == "" or new_pass == "":
            st.error("Username/Password tidak boleh kosong.")
        else:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM users WHERE username=%s", (new_user,))
                if cursor.fetchone():
                    st.error("Username sudah terdaftar.")
                else:
                    create_user(new_user, new_pass, "user")
                    st.success("Registrasi berhasil! Anda telah terdaftar sebagai pengguna.")
                    st.session_state.page = "login"
                    st.rerun()
            except Exception as e:
                st.error(f"Gagal registrasi: {e}")
            finally:
                cursor.close()
                conn.close()

    if st.button("Kembali ke Login"):
        st.session_state.page = "login"
        st.rerun()
