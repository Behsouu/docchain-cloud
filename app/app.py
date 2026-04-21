from flask import Flask, request, jsonify, render_template_string
import os, hashlib
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, generate_latest

load_dotenv()
app = Flask(__name__)

UPLOADS = Counter('docchain_uploads_total', 'Fichiers uploadés')
ERRORS  = Counter('docchain_errors_total',  'Erreurs')
LATENCY = Histogram('docchain_request_duration_seconds', 'Durée requêtes')

CONN_STR   = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER  = os.getenv('AZURE_CONTAINER_NAME', 'docchain')

HTML = '''
<!DOCTYPE html><html><head><title>DocChain</title></head><body>
<h1>DocChain — Upload de document</h1>
<form method="POST" action="/upload" enctype="multipart/form-data">
  <input type="file" name="file" required>
  <button type="submit">Uploader</button>
</form>
</body></html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/upload', methods=['POST'])
def upload():
    with LATENCY.time():
        if 'file' not in request.files:
            ERRORS.inc()
            return jsonify({'error': 'Aucun fichier'}), 400
        f = request.files['file']
        content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
        try:
            client = BlobServiceClient.from_connection_string(CONN_STR)
            blob   = client.get_blob_client(container=CONTAINER, blob=f.filename)
            blob.upload_blob(content, overwrite=True)
            UPLOADS.inc()
            return jsonify({'hash': file_hash, 'filename': f.filename, 'status': 'uploaded'})
        except Exception as e:
            ERRORS.inc()
            return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)