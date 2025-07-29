# database.py

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

# ⭐⭐ NUOVE FUNZIONI PER LA SEZIONE VOLTI ADMIN ⭐⭐

def get_all_unique_face_ids_with_counts():
    """Recupera tutti i face_id unici e il conteggio delle foto associate a ciascuno."""
    conn = None
    faces_data = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Contiamo quante volte ogni face_id appare (quindi quante foto sono collegate)
        cur.execute('SELECT face_id, COUNT(photo_url) FROM faces GROUP BY face_id ORDER BY face_id;')
        faces_data = cur.fetchall()
    except psycopg2.Error as e:
        print(f"Error getting all unique face IDs with counts: {e}")
    finally:
        if conn:
            conn.close()
    # Restituisce una lista di tuple: [(face_id, count), ...]
    return faces_data

def get_photos_by_single_face_id(face_id):
    """Recupera tutte le URL delle foto associate a un singolo face_id."""
    conn = None
    urls = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT photo_url FROM faces WHERE face_id = %s ORDER BY photo_url;', (face_id,))
        urls = [row[0] for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error getting photos by single face ID {face_id}: {e}")
    finally:
        if conn:
            conn.close()
    return urls

# ⭐⭐ FINE NUOVE FUNZIONI ⭐⭐

if __name__ == '__main__':
    init_db()
    print("Database initialization script executed locally.")
