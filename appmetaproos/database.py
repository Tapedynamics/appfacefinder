import os
import psycopg2
from urllib.parse import urlparse

# Questa è la riga FONDAMENTALE per la produzione su Render.
# Render imposterà automaticamente la variabile d'ambiente 'DATABASE_URL'.
DATABASE_URL = os.environ.get('DATABASE_URL')

# Questo blocco è solo per lo sviluppo locale, se non imposti DATABASE_URL
# nel tuo ambiente di sviluppo (ad esempio con un file .env o variabile di sistema).
# Per il deploy su Render, non verrà usato perché Render imposta DATABASE_URL.
if not DATABASE_URL:
    print("ATTENZIONE: DATABASE_URL non trovato nelle variabili d'ambiente. Usando fallback locale.")
    # Sostituisci con i dettagli di un database PostgreSQL locale per testare
    # se non hai un database locale per i test, puoi anche commentare queste due righe.
    DATABASE_URL = "postgresql://user:password@localhost:5432/nome_del_tuo_db_locale"


def get_db_connection():
    # Verifica se DATABASE_URL è stato impostato
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL non è impostato. Impossibile connettersi al database.")

    # Parsifica l'URL del database per estrarre i dettagli di connessione
    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        database=url.path[1:],  # Il nome del database è dopo la prima '/' nel path
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

        # Comando SQL per creare la tabella 'faces' in PostgreSQL
        # SERIAL PRIMARY KEY è l'equivalente di AUTOINCREMENT in SQLite
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
            conn.rollback() # Annulla la transazione in caso di errore
    finally:
        if conn:
            conn.close()

def add_face_record(face_id, photo_url):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # (%s) sono i segnaposto per psycopg2 (non i '?' di sqlite3)
        # ON CONFLICT DO UPDATE è per gestire record duplicati di face_id
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
    photos = set() # Usa un set per garantire URL unici
    if not face_ids:
        return photos

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Creazione di segnaposto dinamici per la clausola IN
        placeholders = ','.join(['%s'] * len(face_ids))
        cur.execute(f"SELECT photo_url FROM faces WHERE face_id IN ({placeholders});", tuple(face_ids))
        photos = {row[0] for row in cur.fetchall()}
    except psycopg2.Error as e:
        print(f"Error getting photos by face IDs: {e}")
    finally:
        if conn:
            conn.close()
    return photos

# Questo blocco opzionale è per testare l'inizializzazione del DB localmente
if __name__ == '__main__':
    init_db()
    print("Database initialization script executed locally.")
