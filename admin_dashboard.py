import streamlit as st
import pandas as pd
from db2 import create_user, read_users, update_user_role, delete_user

def show_admin_dashboard():
    st.title("Dashboard Admin")

    if not st.session_state.get("logged_in", False) or st.session_state.get("role") != "admin":
        st.error("Anda tidak memiliki izin untuk mengakses halaman ini.")
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.subheader(f"Selamat datang, Admin {st.session_state.username}!")
    st.subheader("Manajemen Pengguna")
    
    user_menu = st.radio("Pilih Operasi", ["Lihat Pengguna", "Tambah Pengguna", "Ubah Peran", "Hapus Pengguna"])

    if user_menu == "Lihat Pengguna":
        st.write("Berikut adalah daftar semua pengguna:")
        users_data = read_users()
        df_users = pd.DataFrame(users_data, columns=["ID", "Username", "Role"])
        st.dataframe(df_users)
    
    elif user_menu == "Tambah Pengguna":
        st.write("Silakan isi detail pengguna baru:")
        new_username = st.text_input("Username Baru")
        new_password = st.text_input("Password Baru", type="password")
        new_role = st.selectbox("Peran", ["user", "admin"])
        if st.button("Tambahkan Pengguna"):
            create_user(new_username, new_password, new_role)
            st.success(f"Pengguna {new_username} berhasil ditambahkan dengan peran {new_role}!")
    
    elif user_menu == "Ubah Peran":
        users_data = read_users()
        usernames = [row[1] for row in users_data]
        selected_username = st.selectbox("Pilih Pengguna", usernames)
        new_role_update = st.selectbox("Ubah Peran menjadi", ["user", "admin"])
        if st.button("Perbarui Peran"):
            update_user_role(selected_username, new_role_update)
            st.success(f"Peran pengguna {selected_username} berhasil diubah menjadi {new_role_update}!")
    
    elif user_menu == "Hapus Pengguna":
        users_data = read_users()
        usernames = [row[1] for row in users_data]
        selected_username_delete = st.selectbox("Pilih Pengguna yang akan Dihapus", usernames)
        if st.button("Hapus Pengguna"):
            delete_user(selected_username_delete)
            st.success(f"Pengguna {selected_username_delete} berhasil dihapus!")

    st.markdown("---")
    if st.button("🚪 Keluar"):
        st.session_state.logged_in = False
        st.rerun()
