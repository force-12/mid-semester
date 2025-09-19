import streamlit as st
import subprocess
import json
import re
import os
from db2 import create_media_post, read_media_posts_with_id, update_media_title, delete_media_post

def show_user_dashboard():
    """
    Menampilkan dashboard pengguna untuk mengunggah dan mengunduh tautan media sosial.
    """
    st.title("Dashboard Pengguna")

    if not st.session_state.get("logged_in", False) or st.session_state.get("role") != "user":
        st.error("Anda tidak memiliki izin untuk mengakses halaman ini.")
        st.session_state.logged_in = False
        st.rerun()

    st.write(f"Selamat datang, **{st.session_state.username}**!")
    
    st.sidebar.subheader("Menu")
    menu = st.sidebar.radio("Pilih Opsi", ["Unggah Tautan", "Lihat & Kelola Unggahan"])

    if menu == "Unggah Tautan":
        st.subheader("Unggah Tautan Media Sosial")
        
        # Initialize session state for formats if not present
        if 'available_formats' not in st.session_state:
            st.session_state.available_formats = {"video": {}, "audio": {}}
            st.session_state.current_url = ""

        link_url = st.text_input("Tempel tautan video (YouTube, TikTok, dll.)")

        # Analyze link if it's a new URL
        if link_url and link_url != st.session_state.current_url:
            st.session_state.current_url = link_url
            st.info("Menganalisis tautan untuk format yang tersedia...")
            try:
                # Use yt-dlp to get available formats in JSON format
                command = ["yt-dlp", "--dump-json", link_url]
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    info_dict = json.loads(stdout.decode("utf-8"))
                    formats = info_dict.get('formats', [])
                    
                    st.write(f"Total formats ditemukan: {len(formats)}")
                    
                    # Debug checkbox
                    if st.checkbox("Tampilkan format debug (untuk troubleshooting)"):
                        for i, f in enumerate(formats[:10]):  # Tampilkan 10 format pertama
                            st.write(f"Format {i}: ID={f.get('format_id')}, vcodec={f.get('vcodec')}, acodec={f.get('acodec')}, ext={f.get('ext')}, height={f.get('height')}, abr={f.get('abr')}")
                    
                    video_formats = {}
                    audio_formats = {}
                    
                    # IMPROVED FORMAT FILTERING
                    for f in formats:
                        # Filter VIDEO formats - hanya yang punya resolusi dan tanpa audio
                        if (f.get('vcodec') != 'none' and 
                            f.get('vcodec') is not None and 
                            f.get('height') and 
                            (f.get('acodec') == 'none' or f.get('acodec') is None)):
                            
                            resolution = f.get('height')
                            fps = f.get('fps', '')
                            ext = f.get('ext', '')
                            
                            # Buat label yang informatif untuk video
                            if fps and fps != 'none':
                                label = f"{resolution}p {fps}fps ({ext})"
                            else:
                                label = f"{resolution}p ({ext})"
                            
                            # Hindari duplikat, pilih yang terbaik
                            if label not in video_formats:
                                video_formats[label] = f['format_id']
                        
                        # Untuk AUDIO, kita tidak perlu filter individual formats
                        # Kita akan menggunakan preset "bestaudio" langsung
                    
                    # Sort video formats berdasarkan resolusi (tertinggi ke terendah)
                    if video_formats:
                        sorted_video = {}
                        for label in sorted(video_formats.keys(), 
                                          key=lambda x: int(re.search(r'(\d+)p', x).group(1)) if re.search(r'(\d+)p', x) else 0, 
                                          reverse=True):
                            sorted_video[label] = video_formats[label]
                        video_formats = sorted_video
                    
                    # Untuk audio, kita selalu gunakan preset "bestaudio" (kualitas terbaik otomatis)
                    audio_formats = {
                        "Audio Terbaik": "bestaudio"
                    }
                    
                    st.session_state.available_formats = {
                        "video": video_formats,
                        "audio": audio_formats
                    }
                    
                    st.success(f"Analisis selesai. Ditemukan {len(video_formats)} format video dan {len(audio_formats)} format audio.")
                    
                    # Display found formats for user information
                    col1, col2 = st.columns(2)
                    with col1:
                        if video_formats:
                            st.write("**Format Video Tersedia:**")
                            for label in list(video_formats.keys())[:5]:  # Tampilkan 5 teratas
                                st.write(f"• {label}")
                            if len(video_formats) > 5:
                                st.write(f"... dan {len(video_formats)-5} format lainnya")
                    with col2:
                        if audio_formats:
                            st.write("**Format Audio:**")
                            st.write("• Audio Terbaik (Bitrate tertinggi otomatis)")
                else:
                    st.error(f"Gagal menganalisis tautan: {stderr.decode('utf-8')}")
                    st.session_state.available_formats = {"video": {}, "audio": {}}
            except Exception as e:
                st.error(f"Terjadi kesalahan saat menganalisis tautan: {e}")
                st.session_state.available_formats = {"video": {}, "audio": {}}
        
        if st.session_state.available_formats['video'] or st.session_state.available_formats['audio']:
            with st.form("upload_link_form", clear_on_submit=True):
                title = st.text_input("Judul Unggahan")
                
                download_type = st.radio("Pilih tipe unduhan:", ("Video", "Audio"))
                
                selected_format_id = None
                
                if download_type == "Video":
                    quality_options = list(st.session_state.available_formats["video"].keys())
                    if quality_options:
                        st.info("💡 Pilih resolusi video yang diinginkan:")
                        selected_label = st.selectbox("Resolusi Video:", quality_options, 
                                                    help="Format: Resolusi (fps) - container")
                        selected_format_id = st.session_state.available_formats["video"][selected_label]
                        st.success(f"✅ Akan mengunduh video {selected_label} + audio terbaik")
                    else:
                        st.warning("❌ Tidak ada format video yang ditemukan. Coba pilih 'Audio' saja.")
                        selected_format_id = None
                        
                else: # Audio
                    st.info("🎵 Audio akan diunduh dengan kualitas bitrate terbaik secara otomatis")
                    selected_format_id = "bestaudio"  # Langsung set ke bestaudio
                    st.success("✅ Akan mengunduh audio dengan kualitas terbaik")

                submitted = st.form_submit_button("Unggah & Unduh")

                if submitted and link_url and selected_format_id:
                    try:
                        if not re.match(r"https?://", link_url):
                            st.error("Tautan tidak valid. Harap masukkan tautan yang dimulai dengan http:// atau https://")
                            st.stop()

                        create_media_post(st.session_state.username, title, link_url)
                        st.success("Tautan berhasil diunggah!")

                        st.info("Memulai proses unduhan...")

                        download_dir = "downloads"
                        if not os.path.exists(download_dir):
                            os.makedirs(download_dir)

                        sanitized_title = re.sub(r'[\\/:*?"<>|]', '', title).replace(' ', '_')
                        output_path = os.path.join(download_dir, sanitized_title)
                        
                        if download_type == "Video":
                            # Download video with selected format and best audio
                            command = ["yt-dlp", "-f", f"{selected_format_id}+bestaudio", "-o", f"{output_path}.%(ext)s", link_url]
                        else: # Audio
                            # Download only the selected audio format
                            command = ["yt-dlp", "-f", selected_format_id, "-o", f"{output_path}.%(ext)s", link_url]
                        
                        st.text(f"Perintah: {' '.join(command)}")

                        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout, stderr = process.communicate()

                        if process.returncode == 0:
                            st.success(f"Berhasil mengunduh sebagai {download_type}!")
                            st.text_area("Log Unduhan:", value=stdout.decode("utf-8"), height=200)
                        else:
                            st.error(f"Gagal mengunduh: {stderr.decode('utf-8')}")
                            st.text_area("Log Unduhan:", value=stderr.decode("utf-8"), height=200)

                    except Exception as e:
                        st.error(f"Gagal mengunggah atau mengunduh tautan: {e}")
                
                elif submitted and not link_url:
                    st.error("Silakan masukkan tautan untuk diunggah.")
    
    elif menu == "Lihat & Kelola Unggahan":
        st.subheader("Daftar Tautan Saya")
        user_media = read_media_posts_with_id(st.session_state.username)
        
        if user_media:
            for media in user_media:
                media_id, title, url, timestamp = media
                
                with st.expander(f"Tautan: {title} ({timestamp.strftime('%Y-%m-%d %H:%M')})"):
                    st.write(f"Tautan asli: [{url}]({url})")
                    
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
                                delete_media_post(media_id)
                                st.success("Unggahan berhasil dihapus!")
                                st.rerun()
                    
                st.markdown("---")
        else:
            st.info("Anda belum mengunggah tautan apa pun.")

    st.markdown("---")
    if st.button("🚪 Keluar"):
        st.session_state.logged_in = False
        st.rerun()