# image_processor.py

import os
from deepface import DeepFace
from PIL import Image
import config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def preprocess_image(image_path):
    """Ridimensiona l'immagine per non crashare."""
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img.thumbnail(config.MAX_IMAGE_SIZE)
        img.save(image_path, "JPEG", quality=90)
        logging.info(f"Immagine ridimensionata: {image_path}")
        return True
    except Exception as e:
        logging.error(f"Errore nel pre-processing di {image_path}: {e}")
        return False

def find_faces_in_image(image_path):
    """Analizza l'immagine e trova le corrispondenze."""
    if not os.path.exists(image_path):
        logging.error(f"File non trovato: {image_path}")
        return None

    if not preprocess_image(image_path):
        return None

    logging.info(f"Avvio analisi per: {image_path}")
    try:
        result_dfs = DeepFace.find(
            img_path=image_path,
            db_path=config.DB_PATH,
            enforce_detection=False
        )
        
        if not result_dfs or result_dfs[0].empty:
            logging.info(f"Nessuna corrispondenza per {image_path}")
            return []

        matches = result_dfs[0]['identity'].tolist()
        logging.info(f"Corrispondenze per {image_path}: {matches}")
        return matches
    except Exception as e:
        logging.error(f"Errore DeepFace su {image_path}: {e}")
        return None