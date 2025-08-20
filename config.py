# config.py

# Percorsi cartelle
DB_PATH = "./BDD"
UPLOAD_FOLDER = "./images_to_process"
RESULTS_FOLDER = "./results"

# Impostazioni per la coda di lavori (Redis)
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_QUEUE_NAME = "image_queue"

# Impostazioni per ridurre le immagini
MAX_IMAGE_SIZE = (1500, 1500)