import os

class Config:
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'your-aws-access-key')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'your-aws-secret-key')
    AWS_REGION = os.environ.get('AWS_REGION', 'eu-central-1') # Esempio di regione

    # S3 Configuration
    S3_GALLERY_BUCKET = os.environ.get('S3_GALLERY_BUCKET', 'gallria-photo-metaproos')
    S3_SELFIE_BUCKET = os.environ.get('S3_SELFIE_BUCKET', 'metaproos-client-selfies') # Ho notato questo nuovo bucket, assicurati di configurarlo su AWS!

    # Rekognition Configuration
    REKOGNITION_COLLECTION_ID = os.environ.get('REKOGNITION_COLLECTION_ID', 'facceescursioni')

    TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Create temp directory if it doesn't exist
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    # Admin Password
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin') # CAMBIA QUESTA PASSWORD IN UNA FORTE!

    # ⭐⭐ AGGIUNTA QUI: ⭐⭐
    # Segreto per le sessioni di Flask. ESSENZIALE!
    # Questo valore di fallback 'a_very_secret_and_long_random_string_for_development'
    # È SOLO PER SVILUPPO LOCALE. In produzione su Render, useremo la variabile d'ambiente.
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'a_very_secret_and_long_random_string_for_development')
    # ⭐⭐ FINE AGGIUNTA ⭐⭐
