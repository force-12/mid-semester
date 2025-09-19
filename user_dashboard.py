import streamlit as st
import json
import re
import os
import requests
from db2 import create_media_post, read_media_posts_with_id, update_media_title, delete_media_post

def download_via_api(link_url, download_type, quality=None):
    """
    Menggunakan API pihak ketiga untuk mengunduh konten
    """
    try:
        # API gratis untuk download YouTube (contoh)
        if "youtube.com" in link_url or "youtu.be" in link_url:
            # Gunakan API YouTube downloader
            api_url = f"https://youtube-downloader8.p.rapidapi.com/"
            headers = {
                         'x-rapidapi-key': "b7ef26d5bamshfae6282622bcdedp1915cbjsn873e67b6c660",
                         'x-rapidapi-host': "all-video-downloader3.p.rapidapi.com",
                    }

            params = {
                "url": link_url,
                "format": "mp4" if download_type == "Video" else "mp3"
            }
            
            response = requests.get(api_url, headers=headers, params=params, stream=True)
            return response
            
        # Untuk platform lain, bisa ditambahkan API yang sesuai
        else:
            st.error("Platform ini belum didukung untuk download langsung")
            return None
            
    except Exception as e:
        st.error(f"Error accessing API: {e}")
        return None

def get_direct_download_link(link_url):
    """
    Mendapatkan direct download link menggunakan API
    """
    try:
        # Service untuk mendapatkan direct link
        api_url = "https://social-media-video-downloader.p.rapidapi.com/smvd/get/all"
        headers = {
            "X-RapidAPI-Key": "your-api-key-here",
            "X-RapidAPI-Host": "social-media-video-downloader.p.rapidapi.com"
        }
        
        params = {"url": link_url}
        response = requests.get(api_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data
        return None
        
    except Exception as e:
        st.error(f"Error getting direct link: {e}")
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
        
        link_url = st.text_input("Tempel tautan video (YouTube, TikTok, Instagram, dll.)")

        if link_url:
            st.info("🔍 Menganalisis tautan...")
            
            # Coba dapatkan direct download links
            video_data = get_direct_download_link(link_url)
            
            if video_data:
                st.success("✅ Tautan berhasil dianalisis!")
                
                # Tampilkan preview jika available
                if 'thumbnail' in video_data:
                    st.image(video_data['thumbnail'], caption="Thumbnail Video", width=300)
                
            else:
                st.warning("⚠️ Tidak bisa menganalisis tautan secara otomatis")

        if link_url:
            with st.form("upload_link_form", clear_on_submit=True):
                title = st.text_input("Judul Unggahan")
                
                download_type = st.radio("Pilih tipe unduhan:", ("Video", "Audio"))
                
                quality = st.selectbox("Kualitas:", 
                                    ["720p", "480p", "360p", "240p"] if download_type == "Video" else ["Terbaik"])
                
                submitted = st.form_submit_button("Unggah & Unduh")

                if submitted and link_url:
                    try:
                        if not re.match(r"https?://", link_url):
                            st.error("Tautan tidak valid. Harap masukkan tautan yang dimulai dengan http:// atau https://")
                            st.stop()

                        create_media_post(st.session_state.username, title, link_url)
                        st.success("Tautan berhasil diunggah!")

                        st.info("⏳ Mempersiapkan unduhan...")
                        
                        # Method 1: Direct download link
                        st.info("🔄 Mencoba Method 1: Direct download...")
                        direct_data = get_direct_download_link(link_url)
                        
                        if direct_data and 'links' in direct_data:
                            # Cari link download yang sesuai
                            for link_info in direct_data['links']:
                                if (download_type == "Video" and link_info.get('quality') == quality) or \
                                   (download_type == "Audio" and 'audio' in link_info.get('format', '').lower()):
                                    
                                    download_url = link_info['url']
                                    st.success(f"✅ Direct link ditemukan!")
                                    
                                    # Download langsung ke browser user
                                    response = requests.get(download_url, stream=True)
                                    if response.status_code == 200:
                                        file_extension = ".mp4" if download_type == "Video" else ".mp3"
                                        filename = f"{title}{file_extension}"
                                        
                                        st.download_button(
                                            label="📥 Download Sekarang",
                                            data=response.content,
                                            file_name=filename,
                                            mime="video/mp4" if download_type == "Video" else "audio/mp3"
                                        )
                                        break
                            else:
                                st.warning("❌ Tidak ada direct link yang sesuai")
                                
                                # Method 2: Alternative download options
                                st.info("💡 Alternatif download:")
                                st.markdown(f"""
                                **Opsi 1:** [Download dengan SaveFrom.net](https://en.savefrom.net/16/?url={link_url})
                                **Opsi 2:** [Download dengan Y2mate](https://www.y2mate.com/youtube/{link_url})
                                **Opsi 3:** [Download dengan SSYouTube](https://ssyoutube.com/en{link_url})
                                """)
                                
                        else:
                            st.warning("❌ Tidak bisa mendapatkan direct link")
                            
                            # Tampilkan alternatif
                            st.info("💡 **Alternatif Download:**")
                            st.markdown(f"""
                            Silakan gunakan salah satu layanan download berikut:
                            - [SaveFrom.net](https://en.savefrom.net/16/?url={link_url})
                            - [Y2mate](https://www.y2mate.com/youtube/{link_url})
                            - [SSYouTube](https://ssyoutube.com/en{link_url})
                            """)

                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.info("""
                        **Tips:** 
                        - Pastikan link valid dan tidak private
                        - Coba lagi dalam beberapa menit
                        - Gunakan layanan download alternatif di atas
                        """)
                
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
                    
                    # Tombol download cepat
                    st.markdown(f"""
                    **Download Cepat:**
                    - [SaveFrom.net](https://en.savefrom.net/16/?url={url})
                    - [Y2mate](https://www.y2mate.com/youtube/{url})
                    """)
                    
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

    # Informasi penting
    st.markdown("---")
    st.info("""
    **Catatan Penting:**
    - Download dilakukan melalui layanan pihak ketiga
    - Pastikan Anda memiliki izin untuk mendownload konten
    - Beberapa video mungkin tidak bisa didownload karena pembatasan
    """)
    
    if st.button("🚪 Keluar"):
        st.session_state.logged_in = False
        st.rerun()