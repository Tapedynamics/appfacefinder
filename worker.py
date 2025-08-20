# worker.py

import redis
import config
import logging
import time
import os
import json
from image_processor import find_faces_in_image

r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - WORKER - %(message)s')

def save_result(image_path, matches):
    """Salva i risultati in un file JSON."""
    result_filename = os.path.basename(image_path) + ".json"
    result_path = os.path.join(config.RESULTS_FOLDER, result_filename)
    
    with open(result_path, 'w') as f:
        json.dump({'source_image': image_path, 'matches': matches}, f, indent=4)
    logging.info(f"Risultato salvato in: {result_path}")

def main():
    logging.info("Worker avviato. In attesa di lavori...")
    while True:
        try:
            # blpop attende in modo efficiente un messaggio dalla coda
            _, job_data = r.blpop(config.REDIS_QUEUE_NAME)
            image_path = job_data.decode('utf-8')
            logging.info(f"Lavoro ricevuto: {image_path}")
            
            matches = find_faces_in_image(image_path)
            
            if matches is not None:
                save_result(image_path, matches)
            else:
                logging.warning(f"Analisi fallita per {image_path}.")
        except Exception as e:
            logging.error(f"Errore nel worker: {e}")
            time.sleep(1)

if __name__ == "__main__":
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(config.RESULTS_FOLDER, exist_ok=True)
    main()