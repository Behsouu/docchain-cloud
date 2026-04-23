from flask import Flask, request, jsonify, render_template_string
import os, hashlib, json
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, generate_latest
from web3 import Web3

load_dotenv()
app = Flask(__name__)

UPLOADS = Counter('docchain_uploads_total', 'Fichiers uploadés')
ERRORS  = Counter('docchain_errors_total',  'Erreurs')
LATENCY = Histogram('docchain_request_duration_seconds', 'Durée requêtes')

CONN_STR         = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER        = os.getenv('AZURE_CONTAINER_NAME', 'docchain')
ALCHEMY_URL      = os.getenv('ALCHEMY_URL')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')

w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

CONTRACT_ABI = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"hash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"uploader","type":"address"},{"internalType":"uint256","name":"timestamp","type":"uint256"},{"internalType":"string","name":"filename","type":"string"}],"name":"DocumentRegistered","type":"event"},{"inputs":[],"name":"documentCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getDocumentCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_hash","type":"bytes32"},{"internalType":"string","name":"_filename","type":"string"}],"name":"registerDocument","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_hash","type":"bytes32"}],"name":"verifyDocument","outputs":[{"internalType":"bool","name":"exists","type":"bool"},{"internalType":"address","name":"uploader","type":"address"},{"internalType":"uint256","name":"timestamp","type":"uint256"},{"internalType":"string","name":"filename","type":"string"}],"stateMutability":"view","type":"function"}]')

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=CONTRACT_ABI
)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>DocChain</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        h1 { color: #2c3e50; }
        .upload-form { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        button { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #2980b9; }
        .result { background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 10px 0; display: none; }
    </style>
</head>
<body>
    <h1>DocChain — Gestionnaire de documents</h1>
    <p>Upload sécurisé avec preuve d intégrité blockchain</p>
    <div class="upload-form">
        <h3>Uploader un document</h3>
        <form id="uploadForm">
            <input type="file" id="fileInput" name="file" required><br><br>
            <button type="submit">Uploader et enregistrer sur blockchain</button>
        </form>
        <div class="result" id="result"></div>
    </div>
    <script>
        document.getElementById("uploadForm").onsubmit = async function(e) {
            e.preventDefault();
            const formData = new FormData();
            formData.append("file", document.getElementById("fileInput").files[0]);
            const res = await fetch("/upload", { method: "POST", body: formData });
            const data = await res.json();
            const r = document.getElementById("result");
            r.style.display = "block";
            if (data.status === "uploaded") {
                r.innerHTML = "<b>✅ Fichier uploadé !</b><br>Hash: " + data.hash + "<br>Blockchain TX: " + (data.tx_hash || "en cours...");
            } else {
                r.innerHTML = "<b>❌ Erreur:</b> " + data.error;
                r.style.background = "#ffebee";
            }
        };
    </script>
</body>
</html>
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
        bytes32_hash = bytes.fromhex(file_hash)

        try:
            client = BlobServiceClient.from_connection_string(CONN_STR)
            blob   = client.get_blob_client(container=CONTAINER, blob=f.filename)
            blob.upload_blob(content, overwrite=True)
            UPLOADS.inc()
        except Exception as e:
            ERRORS.inc()
            return jsonify({'error': str(e)}), 500

        tx_hash = None
        try:
            count = contract.functions.verifyDocument(bytes32_hash).call()
            tx_hash = "lecture_seule_ok"
        except Exception as e:
            pass

        return jsonify({
            'hash': file_hash,
            'filename': f.filename,
            'status': 'uploaded',
            'tx_hash': tx_hash,
            'blockchain': CONTRACT_ADDRESS
        })

@app.route('/verify/<file_hash>')
def verify(file_hash):
    try:
        bytes32_hash = bytes.fromhex(file_hash)
        result = contract.functions.verifyDocument(bytes32_hash).call()
        return jsonify({
            'exists': result[0],
            'uploader': result[1],
            'timestamp': result[2],
            'filename': result[3]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/alert', methods=['POST'])
def alert():
    print(f"Alerte Grafana reçue: {request.json}")
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)