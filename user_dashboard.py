import streamlit as st
import pandas as pd
import uuid
from db2 import create_media_post, read_media_posts_with_id, update_media_title, delete_media_post
from supabase import create_client, Client

def show_user_dashboard():
    st.title("Dashboard Pengguna")

    if not st.session_state.get("logged_in", False) or st.session_state.get("role") != "user":
        st.error("Anda tidak memiliki izin untuk mengakses halaman ini.")
        st.session_state.logged_in = False
        st.rerun()

    supabase_url = "https://wxbswpqczzufiqslqist.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind4YnN3cHFjenp1Zmlxc2xxaXN0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyODQ3NDcsImV4cCI6MjA3Mzg2MDc0N30.0c32gc-nSqdHgLtgAXKpuog3yPvx0UWLDKI-JgkSggM"
    
    supabase: Client = create_client(supabase_url, supabase_key)
    bucket_name = "user-media"

    st.write(f"Selamat datang, **{st.session_state.username}**!")
    
    st.sidebar.subheader("Menu")
    menu = st.sidebar.radio("Pilih Opsi", ["Unggah Media", "Lihat & Kelola Unggahan"])

    if menu == "Unggah Media":
        st.subheader("Unggah Foto atau Video")
        with st.form("upload_form", clear_on_submit=True):
            file = st.file_uploader("Pilih file (JPG, PNG, MP4, dll.)", type=["jpg", "jpeg", "png", "mp4", "mov"], help="Ukuran maksimal 200MB.")
            title = st.text_input("Judul Unggahan")
            submitted = st.form_submit_button("Unggah")

            if submitted and file:
                try:
                    # ================== Debug info ==================
                    file_bytes = file.getvalue()
                    file_extension = file.name.split('.')[-1]
                    file_path = f"{uuid.uuid4()}.{file_extension}"
                    st.write(f"Debug: File size: {len(file_bytes)} bytes")
                    st.write(f"Debug: File path: {file_path}")
                    # ===============================================

                    # Upload file ke Supabase Storage
                    result = supabase.storage.from_(bucket_name).upload(file=file_bytes, path=file_path)
                    st.write(f"Debug: Upload result: {result}")  # debug upload

                    # Dapatkan URL publik
                    media_url = supabase.storage.from_(bucket_name).get_public_url(path=file_path)
                    st.write(f"Debug: Media URL: {media_url}")  # debug URL

                    # Simpan metadata ke database
                    create_media_post(st.session_state.username, title, media_url)
                    st.success("File berhasil diunggah!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal mengunggah file: {e}")
                    st.write(f"Debug: Error type: {type(e)}")
            
            elif submitted and not file:
                st.error("Silakan pilih file untuk diunggah.")
    
    elif menu == "Lihat & Kelola Unggahan":
        st.subheader("Unggahan Saya")
        user_media = read_media_posts_with_id(st.session_state.username)
        
        if user_media:
            for media in user_media:
                media_id, title, url, timestamp = media
                with st.expander(f"Unggahan: {title} ({timestamp.strftime('%Y-%m-%d %H:%M')})"):
                    if any(ext in url for ext in ['.jpg', '.jpeg', '.png']):
                        st.image(url, caption=title)
                    elif any(ext in url for ext in ['.mp4', '.mov']):
                        st.video(url, format="video/mp4")
                    else:
                        st.write(f"Tipe file tidak didukung: {url}")
                    
                    with st.form(f"edit_form_{media_id}", clear_on_submit=False):
                        new_title = st.text_input("Judul baru", value=title)
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Ubah Judul"):
                                update_media_title(media_id, new_title)
                                st.success("Judul berhasil diubah!")
                                st.rerun()
                        with col2:
                            if st.form_submit_button("Hapus"):
                                file_path_to_delete = url.split(f"/{bucket_name}/")[-1]
                                supabase.storage.from_(bucket_name).remove([file_path_to_delete])
                                delete_media_post(media_id)
                                st.success("Unggahan berhasil dihapus!")
                                st.rerun()
                st.markdown("---")
        else:
            st.info("Anda belum mengunggah media apa pun.")

    st.markdown("---")
    if st.button("🚪 Keluar"):
        st.session_state.logged_in = False
        st.rerun()
