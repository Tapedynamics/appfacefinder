import mimetypes
from PIL import Image
import os
import boto3
# import sqlite3 # Non più necessario se usi PostgreSQL
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
import uuid
# Importa TUTTE le funzioni del database, incluse le nuove per i volti
from database import init_db, add_face_record, get_photos_by_face_ids, get_all_photos, \
                     delete_all_face_records, get_all_unique_face_ids_with_counts, get_photos_by_single_face_id
from config import Config

# Inizializzazione dell'applicazione Flask. Questa riga è FONDAMENTALE e deve essere qui.
app = Flask(__name__)
# Imposta la chiave segreta per le sessioni da Config (letta dalla variabile d'ambiente FLASK_SECRET_KEY)
app.secret_key = Config.SECRET_KEY

# Inizializza il database (creerà la tabella 'faces' se non esiste)
init_db()

# Inizializzazione dei client AWS S3 e Rekognition
# Le credenziali e la regione sono lette automaticamente dalle variabili d'ambiente grazie a boto3
s3_client = boto3.client('s3', region_name=Config.AWS_REGION)
rekognition_client = boto3.client('rekognition', region_name=Config.AWS_REGION)

def allowed_file(filename):
    """Controlla se l'estensione del file è consentita."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Pagina principale per i clienti per il login con riconoscimento facciale."""
    return render_template('index.html')

# ROUTE ADMIN PRINCIPALE (con gestione login/logout)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Pannello admin per l'upload di foto e gestione. Gestisce anche il login."""
    
    # Debugging prints - utili per capire il flusso nei log di Render
    print(f"--- ADMIN ACCESS ATTEMPT ---")
    print(f"Request Method: {request.method}")
    print(f"Current session['logged_in_admin'] before check: {session.get('logged_in_admin')}")

    # Logica per gestire la richiesta POST (invio del form di login)
    if request.method == 'POST':
        password = request.form.get('password')
        print(f"Submitted Password (first 3 chars): {password[:3]}***")
        print(f"Configured Admin Password (first 3 chars): {Config.ADMIN_PASSWORD[:3]}***")
        
        if password == Config.ADMIN_PASSWORD:
            print("Password match! Setting session['logged_in_admin'] = True")
            session['logged_in_admin'] = True # Imposta la variabile di sessione a True
            flash('Logged in successfully!', 'success') # Messaggio di successo
            return redirect(url_for('admin')) # Reindirizza per ricaricare la pagina admin autenticata
        else:
            print("Password MISMATCH!")
            flash('Invalid password', 'danger') # Messaggio di errore
            return render_template('admin.html', logged_in=False) # Rendi il template con il form di login

    # Logica per gestire la richiesta GET (visualizzazione della pagina)
    # o dopo un login fallito: controlla se l'utente è già loggato
    if not session.get('logged_in_admin'):
        print("Not logged in. Rendering login form.")
        return render_template('admin.html', logged_in=False) # Mostra la pagina di login (form)
    else:
        print("Already logged in. Rendering full admin panel.")
        return render_template('admin.html', logged_in=True) # Mostra il pannello admin completo

# ROUTE LOGOUT ADMIN
@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Gestisce il logout dell'admin."""
    session.pop('logged_in_admin', None) # Rimuove la variabile di sessione
    flash('You have been logged out.', 'info') # Messaggio di logout
    return redirect(url_for('admin')) # Reindirizza alla pagina di login dell'admin

@app.route('/admin/upload', methods=['POST'])
def upload_photos():
    """Gestisce l'upload di foto dal pannello admin."""
    # Protezione: Assicurati che l'admin sia loggato prima di permettere l'upload
    if not session.get('logged_in_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('admin'))

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

                # Percorso per l'immagine da inviare a Rekognition (potrebbe essere ridimensionata)
                rekognition_image_path = original_temp_path
                
                # Logica di ridimensionamento per Rekognition se il file è troppo grande
                if os.path.getsize(original_temp_path) > 15 * 1024 * 1024: # 15MB limite Rekognition
                    resized_temp_path = os.path.join(Config.TEMP_DIR, "resized-" + unique_filename)
                    with Image.open(original_temp_path) as img:
                        img.thumbnail((1920, 1920)) # Ridimensiona mantenendo le proporzioni
                        img.save(resized_temp_path, "JPEG", quality=90)
                    rekognition_image_path = resized_temp_path

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
        
        flash('Photos uploaded and indexed successfully!', 'success')
        return redirect(url_for('admin'))
    
    except Exception as e:
        print(f"ADMIN UPLOAD ERROR: {e}")
        flash(f'Error uploading photos: {str(e)}', 'danger')
        return redirect(url_for('admin'))

@app.route('/search', methods=['POST'])
def search_faces():
    """Gestisce la ricerca di riconoscimento facciale per il login del cliente."""
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
                FaceMatchThreshold=98
            )
        
        os.remove(temp_path)
        
        face_ids = [match['Face']['FaceId'] for match in response['FaceMatches']]
        
        if not face_ids:
            return jsonify({'photo_urls': []})

        photo_urls = get_photos_by_face_ids(face_ids)
        
        # Genera URL pre-firmati per un accesso sicuro e temporaneo alle immagini S3
        presigned_urls = []
        for url in photo_urls:
            try:
                object_key = url.split('/')[-1] # Estrai la chiave dell'oggetto dall'URL
                presigned_url = s3_client.generate_presigned_url('get_object',
                                                                 Params={'Bucket': Config.S3_GALLERY_BUCKET,
                                                                         'Key': object_key},
                                                                 ExpiresIn=3600) # URL valido per 1 ora
                presigned_urls.append(presigned_url)
            except Exception as e:
                print(f"Error generating presigned URL for {url}: {e}")

        return jsonify({'photo_urls': presigned_urls if presigned_urls else list(photo_urls)})
    
    except Exception as e:
        print(f"SEARCH ERROR: {e}") 
        return jsonify({'error': str(e)}), 500

@app.route('/gallery')
def gallery():
    """Visualizza la galleria di foto del cliente."""
    photo_urls = request.args.getlist('photos')
    return render_template('gallery.html', photos=photo_urls)

# ROUTE ADMIN: Visualizza tutte le foto caricate
@app.route('/admin/all_photos')
def all_photos_admin():
    """Visualizza tutte le foto caricate per l'admin."""
    # Protezione: Assicurati che l'admin sia loggato
    if not session.get('logged_in_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('admin'))

    try:
        all_photo_urls = get_all_photos()
        return render_template('all_photos.html', photos=all_photo_urls)
    except Exception as e:
        print(f"ERROR displaying all photos: {e}")
        flash(f'Error loading photos: {str(e)}', 'danger')
        return redirect(url_for('admin'))

# ROUTE ADMIN: Gestione dei volti riconosciuti
@app.route('/admin/faces')
def admin_faces():
    """Visualizza tutti i volti riconosciuti con il conteggio delle foto (solo admin)."""
    if not session.get('logged_in_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('admin'))

    try:
        faces_data = get_all_unique_face_ids_with_counts()
        return render_template('admin_faces.html', faces=faces_data)
    except Exception as e:
        print(f"ERROR displaying admin faces: {e}")
        flash(f'Error loading faces: {str(e)}', 'danger')
        return redirect(url_for('admin'))

@app.route('/admin/faces/<face_id>')
def admin_face_photos(face_id):
    """Visualizza tutte le foto collegate a un specifico face_id (solo admin)."""
    if not session.get('logged_in_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('admin'))

    try:
        photo_urls = get_photos_by_single_face_id(face_id)
        return render_template('admin_face_photos.html', face_id=face_id, photos=photo_urls)
    except Exception as e:
        print(f"ERROR displaying photos for face_id {face_id}: {e}")
        flash(f'Error loading photos for this face: {str(e)}', 'danger')
        return redirect(url_for('admin_faces')) # Reindirizza all'elenco dei volti in caso di errore

# ROUTE ADMIN: Cancella tutte le foto
@app.route('/admin/delete_all_photos', methods=['POST'])
def delete_all_photos_admin():
    """Gestisce la cancellazione di tutte le foto da S3 e dal database."""
    if not session.get('logged_in_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('admin'))

    try:
        all_photo_urls = get_all_photos()
        
        objects_to_delete = []
        for url in all_photo_urls:
            object_key = url.split('/')[-1]
            objects_to_delete.append({'Key': object_key})

        if objects_to_delete:
            s3_client.delete_objects(
                Bucket=Config.S3_GALLERY_BUCKET,
                Delete={'Objects': objects_to_delete}
            )
            print(f"Deleted {len(objects_to_delete)} objects from S3.")
        else:
            print("No objects to delete from S3.")

        delete_all_face_records()
        
        flash('All photos deleted from S3 and database!', 'success')
        return redirect(url_for('admin'))
    
    except Exception as e:
        print(f"ERROR deleting all photos: {e}")
        flash(f'Error deleting photos: {str(e)}', 'danger')
        return redirect(url_for('admin'))
