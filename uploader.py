# uploader.py

import os
import redis
from flask import Flask, request, jsonify
import config
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Nessun file"}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "File non valido"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    r.rpush(config.REDIS_QUEUE_NAME, filepath)
    return jsonify({"message": f"File '{filename}' accodato per l'analisi."}), 202

if __name__ == '__main__':
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)