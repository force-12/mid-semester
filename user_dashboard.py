import streamlit as st
import subprocess
import json
import re
import os
import random
import time
import mimetypes
from db2 import create_media_post, read_media_posts_with_id, update_media_title, delete_media_post

def download_with_fallback(link_url, selected_format_id, output_path, download_type):
    """
    Download dengan berbagai fallback method untuk mengatasi 403 error
    """
    # User agents untuk rotate
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    
    # Method 1: Standard dengan user-agent rotation
    user_agent = random.choice(user_agents)
    
    if download_type == "Video":
        command = [
            "yt-dlp", 
            "-f", f"{selected_format_id}+bestaudio",
            "--user-agent", user_agent,
            "--referer", "https://www.youtube.com/",
            "--add-header", "Accept-Language:en-US,en;q=0.9",
            "--no-check-certificate",
            "-o", f"{output_path}.%(ext)s", 
            link_url
        ]
    else:
        command = [
            "yt-dlp", 
            "-f", selected_format_id,
            "--user-agent", user_agent, 
            "--referer", "https://www.youtube.com/",
            "--add-header", "Accept-Language:en-US,en;q=0.9",
            "--no-check-certificate",
            "-o", f"{output_path}.%(ext)s", 
            link_url
        ]
    
    st.info("🔄 Mencoba method 1: Standard download dengan headers...")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        return True, stdout.decode("utf-8"), ""
    
    # Method 2: Dengan delay dan cookies
    st.info("🔄 Method 1 gagal, mencoba method 2: Dengan delay dan cookies...")
    time.sleep(2)  # Delay 2 detik
    
    if download_type == "Video":
        command = [
            "yt-dlp", 
            "-f", f"{selected_format_id}+bestaudio",
            "--user-agent", random.choice(user_agents),
            "--sleep-interval", "1",
            "--max-sleep-interval", "3", 
            "--no-check-certificate",
            "--ignore-errors",
            "-o", f"{output_path}.%(ext)s", 
            link_url
        ]
    else:
        command = [
            "yt-dlp", 
            "-f", selected_format_id,
            "--user-agent", random.choice(user_agents),
            "--sleep-interval", "1", 
            "--max-sleep-interval", "3",
            "--no-check-certificate",
            "--ignore-errors",
            "-o", f"{output_path}.%(ext)s", 
            link_url
        ]
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        return True, stdout.decode("utf-8"), ""
    
    # Method 3: Fallback ke format alternatif
    st.info("🔄 Method 2 gagal, mencoba method 3: Format alternatif...")
    
    if download_type == "Video":
        # Coba format yang lebih umum
        command = [
            "yt-dlp", 
            "-f", "best[height<=720]/best",  # Fallback ke 720p atau terbaik
            "--user-agent", random.choice(user_agents),
            "--no-check-certificate",
            "-o", f"{output_path}.%(ext)s", 
            link_url
        ]
    else:
        command = [
            "yt-dlp", 
            "-f", "bestaudio/best",  # Fallback ke best jika bestaudio gagal
            "--user-agent", random.choice(user_agents),
            "--no-check-certificate", 
            "-o", f"{output_path}.%(ext)s", 
            link_url
        ]
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        return True, stdout.decode("utf-8"), ""
    
    # Method 4: Last resort - paling basic
    st.info("🔄 Method 3 gagal, mencoba method 4: Basic download...")
    
    command = [
        "yt-dlp", 
        "--user-agent", random.choice(user_agents),
        "--no-check-certificate",
        "-o", f"{output_path}.%(ext)s", 
        link_url
    ]
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    return process.returncode == 0, stdout.decode("utf-8"), stderr.decode("utf-8")

def get_downloaded_file_path(output_path):
    """
    Mencari file yang berhasil diunduh berdasarkan output path
    """
    # Cari file dengan pattern output_path.*
    directory = os.path.dirname(output_path)
    filename_prefix = os.path.basename(output_path)
    
    if not os.path.exists(directory):
        return None
        
    for file in os.listdir(directory):
        if file.startswith(filename_prefix):
            return os.path.join(directory, file)
    
    return None

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
                        
                        # Gunakan fungsi download_with_fallback yang baru
                        success, stdout, stderr = download_with_fallback(link_url, selected_format_id, output_path, download_type)

                        if success:
                            st.success(f"✅ Berhasil mengunduh sebagai {download_type}!")
                            
                            # Cari file yang berhasil diunduh
                            downloaded_file_path = get_downloaded_file_path(output_path)
                            
                            if downloaded_file_path and os.path.exists(downloaded_file_path):
                                # Baca file sebagai bytes
                                with open(downloaded_file_path, "rb") as file:
                                    file_bytes = file.read()
                                
                                # Dapatkan nama file dan ekstensi
                                filename = os.path.basename(downloaded_file_path)
                                
                                # Tentukan MIME type berdasarkan ekstensi
                                mime_type, _ = mimetypes.guess_type(downloaded_file_path)
                                if mime_type is None:
                                    mime_type = "application/octet-stream"
                                
                                # Tampilkan tombol download
                                st.download_button(
                                    label="📥 Download File ke Perangkat Anda",
                                    data=file_bytes,
                                    file_name=filename,
                                    mime=mime_type
                                )
                                
                                # Hapus file dari server setelah berhasil ditampilkan
                                try:
                                    os.remove(downloaded_file_path)
                                except:
                                    pass
                            else:
                                st.error("File unduhan tidak ditemukan di server.")
                        else:
                            st.error(f"❌ Semua method download gagal!")
                            st.text_area("📋 Error Log:", value=stderr, height=200)
                            
                            # Saran alternatif untuk user
                            st.info("💡 **Saran alternatif:**")
                            st.write("1. Coba lagi dalam beberapa menit")  
                            st.write("2. Cek apakah link masih valid")
                            st.write("3. Coba dengan link dari platform lain")
                            st.write("4. Untuk YouTube, coba link video yang tidak age-restricted")

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