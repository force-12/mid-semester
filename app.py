import streamlit as st
import pandas as pd
from db2 import create_siswa, read_siswa, update_siswa, delete_siswa, search_siswa

def show_app():
    st.title("CRUD SISWA")

    if not st.session_state.get("logged_in", False):
        st.error("Please login first!")
        st.session_state.page = "login"
        st.rerun()

    menu = st.sidebar.selectbox("Menu", ["Tambah", "Lihat", "Ubah", "Hapus", "Cari Data"])

    if menu == "Tambah":
        NIM = st.text_input("NIM")
        Nama = st.text_input("Nama")
        Angkatan = st.number_input("Angkatan", min_value=2020, max_value=2030, step=1)
        Email = st.text_input("Email")
        if st.button("Simpan"):
            create_siswa(NIM, Nama, Angkatan, Email)
            st.success("Data siswa berhasil ditambahkan!")

    elif menu == "Lihat":
        data = read_siswa()
        df = pd.DataFrame(data, columns=["ID", "NIM", "Nama", "Angkatan", "Email"])
        st.dataframe(df)

    elif menu == "Ubah":
        data = read_siswa()
        if data:
            nims = [row[1] for row in data]
            selected_nim = st.selectbox("Pilih NIM", nims)
            siswa = next((row for row in data if row[1] == selected_nim), None)
            nim_baru = st.text_input("NIM baru", value=siswa[1])
            nama_baru = st.text_input("Nama baru", value=siswa[2])
            angkatan_baru = st.number_input(
                "Angkatan baru", min_value=2020, max_value=2030, step=1, value=siswa[3]
            )
            email_baru = st.text_input("Email baru", value=siswa[4])
            if st.button("Ubah"):
                update_siswa(selected_nim, nama_baru, angkatan_baru, email_baru)
                st.success("Data siswa berhasil diubah!")

    elif menu == "Hapus":
        data = read_siswa()
        if data:
            NIM = st.selectbox("Pilih NIM", [row[1] for row in data])
            if st.button("Hapus"):
                delete_siswa(NIM)
                st.success("Data siswa berhasil dihapus!")

    elif menu == "Cari Data":
        nim_cari = st.text_input("Masukkan NIM yang ingin dicari")
        if st.button("Cari"):
            hasil = search_siswa(nim_cari)
            if hasil:
                df = pd.DataFrame(hasil, columns=["ID", "NIM", "Nama", "Angkatan", "Email"])
                st.dataframe(df)
            else:
                st.warning("Data dengan NIM tersebut tidak ditemukan.")

    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()