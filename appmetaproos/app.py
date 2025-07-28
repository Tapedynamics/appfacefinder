import os

class Config:
    # AWS Configuration
    # Legge le credenziali e la regione dalle variabili d'ambiente.
    # I valori di fallback sono per lo sviluppo locale se le variabili non sono impostate.
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'your-aws-access-key')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'your-aws-secret-key')
    AWS_REGION = os.environ.get('AWS_REGION', 'eu-central-1') # Sostituisci con la tua regione AWS

    # S3 Configuration
    # Nomi dei bucket S3, letti dalle variabili d'ambiente.
    S3_GALLERY_BUCKET = os.environ.get('S3_GALLERY_BUCKET', 'gallria-photo-metaproos') # Il tuo bucket per le foto
    S3_SELFIE_BUCKET = os.environ.get('S3_SELFIE_BUCKET', 'metaproos-client-selfies') # Se usi un bucket separato per i selfie temporanei

    # Rekognition Configuration
    # ID della collection Rekognition, letto dalle variabili d'ambiente.
    REKOGNITION_COLLECTION_ID = os.environ.get('REKOGNITION_COLLECTION_ID', 'facceescursioni')

    # Application Configuration
    # Percorso per i file temporanei (importante per Render, usa /tmp)
    TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')
    # Estensioni di file consentite per l'upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Crea la directory temporanea se non esiste (utile per lo sviluppo locale)
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    # Admin Password
    # Legge la password admin dalle variabili d'ambiente.
    # Il valore di fallback 'admin' è SOLO per lo sviluppo locale, CAMBIALO IN UNA PASSWORD FORTE!
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')

    # Flask Secret Key
    # Chiave segreta per le sessioni di Flask. ESSENZIALE per la sicurezza delle sessioni.
    # Legge la chiave dalle variabili d'ambiente.
    # Il valore di fallback è SOLO per lo sviluppo locale, usa una stringa LUNGA e CASUALE in produzione.
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'a_very_secret_and_long_random_string_for_development')
