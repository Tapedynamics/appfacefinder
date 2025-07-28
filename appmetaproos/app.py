import mimetypes
from PIL import Image # <-- Importa la libreria Pillow
import mimetypes
import os
import boto3
import sqlite3
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
import uuid
from database import init_db, add_face_record, get_photos_by_face_ids, get_all_photos
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Initialize the database
init_db()

# AWS clients
# This assumes credentials are configured via `aws configure` or environment variables
s3_client = boto3.client('s3', region_name=Config.AWS_REGION)
rekognition_client = boto3.client('rekognition', region_name=Config.AWS_REGION)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page for clients to login with facial recognition"""
    return render_template('index.html')

@app.route('/admin/upload', methods=['POST'])
def upload_photos():
    """Handle photo uploads from the admin panel"""
    if 'photos' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    photos = request.files.getlist('photos')
    
    if not photos or photos[0].filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    try:
        for photo in photos:
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
                
                # Salva il file originale in un percorso temporaneo
                original_temp_path = os.path.join(Config.TEMP_DIR, "original-" + unique_filename)
                photo.save(original_temp_path)

                # Percorso per l'immagine da inviare a Rekognition
                rekognition_image_path = original_temp_path
                
                # --- INIZIO NUOVA LOGICA DI RIDIMENSIONAMENTO ---
                
                # Controlla la dimensione del file (in byte). 15MB ≈ 15 * 1024 * 1024 bytes
                if os.path.getsize(original_temp_path) > 15 * 1024 * 1024:
                    # Se il file è troppo grande, crea una versione ridimensionata per l'analisi
                    resized_temp_path = os.path.join(Config.TEMP_DIR, "resized-" + unique_filename)
                    
                    with Image.open(original_temp_path) as img:
                        # Ridimensiona mantenendo le proporzioni, con una larghezza massima di 1920px
                        img.thumbnail((1920, 1920)) 
                        img.save(resized_temp_path, "JPEG", quality=90)
                    
                    # Usa l'immagine ridimensionata per Rekognition
                    rekognition_image_path = resized_temp_path
                
                # --- FINE NUOVA LOGICA ---

                # Indovina il tipo di file dall'originale
                content_type, _ = mimetypes.guess_type(unique_filename)
                if content_type is None:
                    content_type = 'application/octet-stream'

                extra_args = {'ACL': 'public-read', 'ContentType': content_type}
                
                # Carica la FOTO ORIGINALE di alta qualità su S3
                s3_client.upload_file(
                    original_temp_path, 
                    Config.S3_GALLERY_BUCKET, 
                    unique_filename,
                    ExtraArgs=extra_args
                )
                
                s3_url = f"https://{Config.S3_GALLERY_BUCKET}.s3.{Config.AWS_REGION}.amazonaws.com/{unique_filename}"
                
                # Invia l'IMMAGINE OTTIMIZZATA a Rekognition per l'analisi
                with open(rekognition_image_path, 'rb') as image_for_rekognition:
                    response = rekognition_client.index_faces(
                        CollectionId=Config.REKOGNITION_COLLECTION_ID,
                        Image={'Bytes': image_for_rekognition.read()},
                        ExternalImageId=unique_filename,
                        DetectionAttributes=['ALL']
                    )
                
                # Salva i record nel database
                for face_record in response['FaceRecords']:
                    face_id = face_record['Face']['FaceId']
                    add_face_record(face_id, s3_url)
                
                # Pulisci TUTTI i file temporanei
                os.remove(original_temp_path)
                if rekognition_image_path != original_temp_path:
                    os.remove(rekognition_image_path)
        
        flash('Photos uploaded and indexed successfully!')
        return redirect(url_for('admin'))
    
    except Exception as e:
        print(f"ADMIN UPLOAD ERROR: {e}")
        flash(f'Error uploading photos: {str(e)}')
        return redirect(url_for('admin'))

# In app.py, sostituisci la funzione esistente con questa

@app.route('/search', methods=['POST'])
def search_faces():
    """Handle facial recognition search for client login"""
    if 'selfie' not in request.files:
        return jsonify({'error': 'No selfie provided'}), 400
    
    selfie = request.files['selfie']
    
    if selfie.filename == '':
        return jsonify({'error': 'No selfie selected'}), 400
    
    try:
        filename = str(uuid.uuid4()) + '.jpg'
        temp_path = os.path.join(Config.TEMP_DIR, filename)
        selfie.save(temp_path)
        
        with open(temp_path, 'rb') as image:
            response = rekognition_client.search_faces_by_image(
                CollectionId=Config.REKOGNITION_COLLECTION_ID,
                Image={'Bytes': image.read()},
                MaxFaces=5,
                # 👇 LA MODIFICA È QUI: Aumenta la soglia per una maggiore precisione
                FaceMatchThreshold=98
            )
        
        os.remove(temp_path) # Pulisci subito il selfie temporaneo
        
        face_ids = [match['Face']['FaceId'] for match in response['FaceMatches']]
        
        if not face_ids:
            return jsonify({'photo_urls': []})

        photo_urls = get_photos_by_face_ids(face_ids)
        
        # Questa parte è opzionale, ma consigliata se usi gli URL pre-firmati
        presigned_urls = []
        for url in photo_urls:
            try:
                object_key = url.split('/')[-1]
                presigned_url = s3_client.generate_presigned_url('get_object',
                                                                 Params={'Bucket': Config.S3_GALLERY_BUCKET,
                                                                         'Key': object_key},
                                                                 ExpiresIn=3600)
                presigned_urls.append(presigned_url)
            except Exception as e:
                print(f"Error generating presigned URL for {url}: {e}")

        return jsonify({'photo_urls': presigned_urls if presigned_urls else list(photo_urls)})
    
    except Exception as e:
        print(f"SEARCH ERROR: {e}") 
        return jsonify({'error': str(e)}), 500

@app.route('/gallery')
def gallery():
    """Display the client's gallery of photos"""
    photo_urls = request.args.getlist('photos')
    return render_template('gallery.html', photos=photo_urls)
    
@app.route('/admin/all_photos')
def all_photos_admin():
    """Display all uploaded photos for the admin."""
    try:
        all_photo_urls = get_all_photos()
        return render_template('all_photos.html', photos=all_photo_urls)
    except Exception as e:
        print(f"ERROR displaying all photos: {e}")
        flash(f'Error loading photos: {str(e)}')
        return redirect(url_for('admin')) # Reindirizza all'admin panel in caso di errore
        
@app.route('/admin', methods=['GET', 'POST']) # <--- Modifica qui per accettare GET e POST
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == Config.ADMIN_PASSWORD:
            session['logged_in_admin'] = True # Imposta una variabile di sessione
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin')) # Reindirizza per ricaricare la pagina admin autenticata
        else:
            flash('Invalid password', 'danger')
            return render_template('admin.html', logged_in=False) # Rendi il template con messaggio di errore
    
    # Per richieste GET o dopo un login fallito, controlla se l'utente è già loggato
    if not session.get('logged_in_admin'):
        return render_template('admin.html', logged_in=False) # Mostra la pagina di login
    
    # Se l'utente è loggato, mostra il pannello admin completo
    return render_template('admin.html', logged_in=True) # Mostra la pagina admin completa

# app.py (aggiungi questa nuova route)

# ... (le tue altre route) ...

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('logged_in_admin', None) # Rimuove la variabile di sessione
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin')) # Reindirizza alla pagina di login dell'admin
