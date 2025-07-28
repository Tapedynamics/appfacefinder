import sqlite3

DATABASE_NAME = 'faces.db' # O 'faces.dbf' se preferisci quel nome

def get_db_connection():
    """Crea una connessione al database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Inizializza il database creando la tabella 'photos'.
    Questa tabella lega un FaceId a un URL di un'immagine.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            face_id TEXT NOT NULL,
            image_url TEXT NOT NULL,
            UNIQUE(face_id, image_url)
        )
    ''')
    conn.commit()
    conn.close()

def add_face_record(face_id, image_url):
    """Aggiunge un record che collega un face_id a un URL di un'immagine."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO photos (face_id, image_url) VALUES (?, ?)",
            (face_id, image_url)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Ignora l'inserimento se la coppia face_id/image_url esiste già.
        pass
    finally:
        conn.close()

def get_photos_by_face_ids(face_ids):
    """
    Recupera tutti gli URL delle immagini associate a una lista di face_id.
    """
    if not face_ids:
        return set()

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Prepara i '?' per la query IN
    placeholders = ','.join('?' for _ in face_ids)
    query = f"SELECT DISTINCT image_url FROM photos WHERE face_id IN ({placeholders})"
    
    cursor.execute(query, face_ids)
    rows = cursor.fetchall()
    conn.close()
    
    # Restituisce un set di URL unici
    return {row['image_url'] for row in rows}
