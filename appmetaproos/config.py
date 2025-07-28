import os

class Config:
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID') or 'your-aws-access-key'
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY') or 'your-aws-secret-key'
    AWS_REGION = os.environ.get('AWS_REGION') or 'eu-central-1'
    
    # S3 Configuration
    S3_GALLERY_BUCKET = os.environ.get('S3_GALLERY_BUCKET') or 'gallria-photo-metaproos'
    S3_SELFIE_BUCKET = os.environ.get('S3_SELFIE_BUCKET') or 'metaproos-client-selfies'
    
    # Rekognition Configuration
    REKOGNITION_COLLECTION_ID = os.environ.get('REKOGNITION_COLLECTION_ID') or 'facceescursioni'
    
    # Application Configuration
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'faces.db'
    TEMP_DIR = os.environ.get('TEMP_DIR') or 'temp'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Create temp directory if it doesn't exist
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin') # CAMBIA QUESTA PASSWORD IN UNA FORTE!
