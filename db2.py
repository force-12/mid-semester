import psycopg2

def get_connection():
    """
    Fungsi koneksi ke Supabase PostgreSQL
    Mengembalikan objek connection atau None kalau gagal
    """
    try:
        conn = psycopg2.connect(
            "postgresql://postgres.wxbswpqczzufiqslqist:midsemester@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
        )
        print("[DB] Koneksi berhasil!")  # terminal
        return conn
    except Exception as e:
        print(f"[DB] Gagal koneksi: {e}")  # terminal
        return None

# -------------------------
# CRUD Users
# -------------------------
def create_user(username, password, role):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, password, role)
            )
        conn.commit()
        conn.close()

def read_users():
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role FROM users ORDER BY id ASC")
            result = cursor.fetchall()
        conn.close()
        return result
    return []

def update_user_role(username, new_role):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role=%s WHERE username=%s",
                (new_role, username)
            )
        conn.commit()
        conn.close()

def delete_user(username):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE username=%s", (username,))
        conn.commit()
        conn.close()

def get_user_role(username):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT role FROM users WHERE username=%s', (username,))
            result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
    return None

# -------------------------
# CRUD Media Posts - FIXED COLUMN NAMES
# -------------------------
def create_media_post(username, title, media_url):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            # FIXED: Changed 'username' to 'user_id' to match new table structure
            cursor.execute(
                "INSERT INTO media_posts (user_id, title, media_url) VALUES (%s, %s, %s)",
                (username, title, media_url)
            )
        conn.commit()
        conn.close()

def read_media_posts(username):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            # FIXED: Changed 'username' to 'user_id' to match new table structure
            cursor.execute("SELECT id, title, media_url, created_at FROM media_posts WHERE user_id=%s ORDER BY created_at DESC", (username,))
            result = cursor.fetchall()
        conn.close()
        return result
    return []

def update_media_title(media_id, new_title):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE media_posts SET title = %s WHERE id = %s", (new_title, media_id))
        conn.commit()
        conn.close()

def delete_media_post(media_id):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM media_posts WHERE id = %s", (media_id,))
        conn.commit()
        conn.close()

def read_media_posts_with_id(username):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            # FIXED: Changed 'username' to 'user_id' to match new table structure
            cursor.execute("SELECT id, title, media_url, created_at FROM media_posts WHERE user_id=%s ORDER BY created_at DESC", (username,))
            result = cursor.fetchall()
        conn.close()
        return result
    return []