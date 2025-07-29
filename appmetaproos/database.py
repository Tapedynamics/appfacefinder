import os
import psycopg2
from urllib.parse import urlparse

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("ATTENZIONE: DATABASE_URL non trovato nelle variabili d'ambiente. Usando fallback locale.")
    DATABASE_URL = "postgresql://user:password@localhost:5432/nome_del_tuo_db_locale"


def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL non è impostato. Impossibile connettersi al database.")

    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        sslmode='require' # IMPORTANTE: Render richiede connessioni SSL
    )
    return conn

def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS faces (
                id SERIAL PRIMARY KEY,
                face_id TEXT NOT NULL UNIQUE,
                photo_url TEXT NOT NULL
            );
        ''')
        conn.commit()
        print("Database initialized successfully with PostgreSQL!")
    except psycopg2.Error as e:
        print(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def add_face_record(face_id, photo_url):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO faces (face_id, photo_url) VALUES (%s, %s) ON CONFLICT(face_id) DO UPDATE SET photo_url = EXCLUDED.photo_url;",
            (face_id, photo_url)
        )
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error adding face record: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def get_photos_by_face_ids(face_ids):
    conn = None
    photos = set()
    if not face_ids:
        return photos

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        placeholders = ','.join(['%s'] * len(face_ids))
        cur.execute(f"SELECT photo_url FROM faces WHERE face_id IN ({placeholders});", tuple(face_ids))
        photos = {row[0] for row in cur.fetchall()}
    except psycopg2.Error as e:
        print(f"Error getting photos by face IDs: {e}")
    finally:
        if conn:
            conn.close()
    return photos

def get_all_photos():
    conn = None
    photos = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT photo_url FROM faces ORDER BY id DESC;")
        photos = [row[0] for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error getting all photos: {e}")
    finally:
        if conn:
            conn.close()
    return photos

def delete_all_face_records():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM faces;")
        conn.commit()
        print("All face records deleted from database.")
    except psycopg2.Error as e:
        print(f"Error deleting all face records: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialization script executed locally.")
