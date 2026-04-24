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
PRIVATE_KEY      = os.getenv('WALLET_PRIVATE_KEY')

w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL)) if ALCHEMY_URL else None

CONTRACT_ABI = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"hash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"uploader","type":"address"},{"internalType":"uint256","name":"timestamp","type":"uint256"},{"internalType":"string","name":"filename","type":"string"}],"name":"DocumentRegistered","type":"event"},{"inputs":[],"name":"documentCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getDocumentCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_hash","type":"bytes32"},{"internalType":"string","name":"_filename","type":"string"}],"name":"registerDocument","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_hash","type":"bytes32"}],"name":"verifyDocument","outputs":[{"internalType":"bool","name":"exists","type":"bool"},{"internalType":"address","name":"uploader","type":"address"},{"internalType":"uint256","name":"timestamp","type":"uint256"},{"internalType":"string","name":"filename","type":"string"}],"stateMutability":"view","type":"function"}]')

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=CONTRACT_ABI
) if w3 and CONTRACT_ADDRESS else None

def register_on_blockchain(file_hash: str, filename: str) -> str:
    try:
        bytes32_hash = bytes.fromhex(file_hash)
        account      = w3.eth.account.from_key(PRIVATE_KEY)
        nonce        = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.registerDocument(
            bytes32_hash, filename
        ).build_transaction({
            'from'    : account.address,
            'nonce'   : nonce,
            'gas'     : 200000,
            'gasPrice': w3.eth.gas_price,
            'chainId' : 11155111
        })
        signed  = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        return tx_hash.hex()
    except Exception as e:
        print(f"Blockchain error: {e}")
        return None

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>DocChain</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; }
        h1 { color: #2c3e50; }
        .upload-form { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .verify-form { background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0; }
        button { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background: #2980b9; }
        .result { padding: 15px; border-radius: 8px; margin: 10px 0; display: none; word-break: break-all; }
        .success { background: #e8f5e9; border-left: 4px solid #27ae60; }
        .error { background: #ffebee; border-left: 4px solid #e74c3c; }
        input[type=text] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
    </style>
</head>
<body>
    <h1>DocChain</h1>
    <p>Gestionnaire de documents avec preuve d intégrité blockchain sur Ethereum Sepolia</p>
    <div class="upload-form">
        <h3>Uploader un document</h3>
        <form id="uploadForm">
            <input type="file" id="fileInput" name="file" required><br>
            <button type="submit">Uploader et enregistrer sur blockchain</button>
        </form>
        <div class="result" id="uploadResult"></div>
    </div>
    <div class="verify-form">
        <h3>Verifier l integrite d un document</h3>
        <input type="text" id="hashInput" placeholder="Entrez le hash SHA-256 du fichier...">
        <button onclick="verifyDoc()">Verifier sur blockchain</button>
        <div class="result" id="verifyResult"></div>
    </div>
    <script>
        document.getElementById("uploadForm").onsubmit = async function(e) {
            e.preventDefault();
            const r = document.getElementById("uploadResult");
            r.style.display = "block";
            r.className = "result";
            r.innerHTML = "En cours - upload et enregistrement sur blockchain...";
            const formData = new FormData();
            formData.append("file", document.getElementById("fileInput").files[0]);
            const res  = await fetch("/upload", { method: "POST", body: formData });
            const data = await res.json();
            if (data.status === "uploaded") {
                r.className = "result success";
                r.innerHTML = "<b>Fichier uploade et enregistre sur blockchain !</b><br><br>" +
                    "<b>Fichier :</b> " + data.filename + "<br>" +
                    "<b>Hash SHA-256 :</b> " + data.hash + "<br>" +
                    "<b>Transaction blockchain :</b> <a href='https://sepolia.etherscan.io/tx/" + data.tx_hash + "' target='_blank'>" + data.tx_hash + "</a><br>" +
                    "<b>Contrat :</b> " + data.blockchain;
            } else {
                r.className = "result error";
                r.innerHTML = "<b>Erreur :</b> " + (data.error || JSON.stringify(data));
            }
        };
        async function verifyDoc() {
            const hash = document.getElementById("hashInput").value.trim();
            const r    = document.getElementById("verifyResult");
            r.style.display = "block";
            r.innerHTML = "Verification en cours...";
            const res  = await fetch("/verify/" + hash);
            const data = await res.json();
            if (data.exists) {
                r.className = "result success";
                r.innerHTML = "<b>Document authentifie !</b><br>" +
                    "<b>Uploader :</b> " + data.uploader + "<br>" +
                    "<b>Fichier :</b> " + data.filename + "<br>" +
                    "<b>Date :</b> " + new Date(data.timestamp * 1000).toLocaleString();
            } else {
                r.className = "result error";
                r.innerHTML = "<b>Document non trouve dans la blockchain</b>";
            }
        }
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
        f       = request.files['file']
        content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
        try:
            client = BlobServiceClient.from_connection_string(CONN_STR)
            blob   = client.get_blob_client(container=CONTAINER, blob=f.filename)
            blob.upload_blob(content, overwrite=True)
            UPLOADS.inc()
        except Exception as e:
            ERRORS.inc()
            return jsonify({'error': f'Erreur Azure Storage: {str(e)}'}), 500
        tx_hash = register_on_blockchain(file_hash, f.filename)
        return jsonify({
            'hash'      : file_hash,
            'filename'  : f.filename,
            'status'    : 'uploaded',
            'tx_hash'   : tx_hash,
            'blockchain': CONTRACT_ADDRESS
        })

@app.route('/verify/<file_hash>')
def verify(file_hash):
    try:
        bytes32_hash = bytes.fromhex(file_hash)
        result = contract.functions.verifyDocument(bytes32_hash).call()
        return jsonify({
            'exists'   : result[0],
            'uploader' : result[1],
            'timestamp': result[2],
            'filename' : result[3]
        })
    except Exception as e:
        ERRORS.inc()
        return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/alert', methods=['POST'])
def alert():
    print(f"Alerte Grafana recue: {request.json}")
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)