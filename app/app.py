from flask import Flask, request, jsonify, render_template_string
import os, hashlib, json, uuid, threading
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient
from azure.data.tables import TableServiceClient
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, generate_latest
from web3 import Web3

load_dotenv()
app = Flask(__name__)

UPLOADS = Counter('docchain_uploads_total', 'Fichiers uploades')
ERRORS  = Counter('docchain_errors_total',  'Erreurs')
LATENCY = Histogram('docchain_request_duration_seconds', 'Duree requetes')

CONN_STR         = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER        = os.getenv('AZURE_CONTAINER_NAME', 'docchain')
ALCHEMY_URL      = os.getenv('ALCHEMY_URL')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
PRIVATE_KEY      = os.getenv('WALLET_PRIVATE_KEY')
TABLE_NAME       = 'documents'

w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL)) if ALCHEMY_URL else None
CONTRACT_ABI = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"hash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"uploader","type":"address"},{"internalType":"uint256","name":"timestamp","type":"uint256"},{"internalType":"string","name":"filename","type":"string"}],"name":"DocumentRegistered","type":"event"},{"inputs":[],"name":"documentCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getDocumentCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_hash","type":"bytes32"},{"internalType":"string","name":"_filename","type":"string"}],"name":"registerDocument","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_hash","type":"bytes32"}],"name":"verifyDocument","outputs":[{"internalType":"bool","name":"exists","type":"bool"},{"internalType":"address","name":"uploader","type":"address"},{"internalType":"uint256","name":"timestamp","type":"uint256"},{"internalType":"string","name":"filename","type":"string"}],"stateMutability":"view","type":"function"}]')
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI) if w3 and CONTRACT_ADDRESS else None


def save_to_table(filename, file_hash, tx_hash, file_size, row_key=None):
    try:
        tc = TableServiceClient.from_connection_string(CONN_STR).get_table_client(TABLE_NAME)
        tc.create_entity({
            'PartitionKey'    : 'documents',
            'RowKey'          : row_key or str(uuid.uuid4()),
            'filename'        : filename,
            'hash_sha256'     : file_hash,
            'tx_hash'         : tx_hash or '',
            'contract_address': CONTRACT_ADDRESS or '',
            'file_size_bytes' : file_size,
            'uploaded_at'     : datetime.now(timezone.utc).isoformat(),
            'status'          : 'uploaded'
        })
        return True
    except Exception as e:
        print(f"Table Storage error: {e}")
        return False


def get_all_documents():
    try:
        tc = TableServiceClient.from_connection_string(CONN_STR).get_table_client(TABLE_NAME)
        return sorted(list(tc.list_entities()), key=lambda x: x.get('uploaded_at', ''), reverse=True)
    except Exception as e:
        print(f"Table list error: {e}")
        return []


def delete_from_table(row_key):
    try:
        TableServiceClient.from_connection_string(CONN_STR).get_table_client(TABLE_NAME).delete_entity('documents', row_key)
        return True
    except Exception as e:
        print(f"Table delete error: {e}")
        return False


def register_on_blockchain_async(file_hash, filename, row_key):
    """Enregistre sur blockchain en arriere-plan - ne bloque pas l'upload"""
    try:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        tx = contract.functions.registerDocument(
            bytes.fromhex(file_hash), filename
        ).build_transaction({
            'from'    : account.address,
            'nonce'   : w3.eth.get_transaction_count(account.address),
            'gas'     : 200000,
            'gasPrice': w3.eth.gas_price,
            'chainId' : 11155111
        })
        signed  = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hex  = tx_hash.hex()
        print(f"Blockchain TX envoyee: {tx_hex}")
        w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        # Mise a jour de la table avec le tx_hash confirme
        tc = TableServiceClient.from_connection_string(CONN_STR).get_table_client(TABLE_NAME)
        tc.update_entity({
            'PartitionKey': 'documents',
            'RowKey'      : row_key,
            'tx_hash'     : tx_hex
        }, mode='merge')
        print(f"Blockchain TX confirmee: {tx_hex}")
    except Exception as e:
        print(f"Blockchain async error: {e}")


HTML = """<!DOCTYPE html>
<html>
<head>
<title>DocChain - LegalVault</title>
<meta charset="utf-8">
<style>
*{box-sizing:border-box}
body{font-family:Arial,sans-serif;max-width:900px;margin:30px auto;padding:20px;background:#f5f6fa}
h1{color:#2c3e50;margin-bottom:5px}
.sub{color:#7f8c8d;margin-bottom:25px;font-size:14px}
.card{background:white;border-radius:8px;padding:20px;margin-bottom:20px;box-shadow:0 2px 6px rgba(0,0,0,.08)}
.card h3{color:#2c3e50;margin-top:0;border-bottom:2px solid #3498db;padding-bottom:8px}
.btn{background:#3498db;color:white;padding:10px 20px;border:none;border-radius:4px;cursor:pointer;font-size:14px;margin-top:8px}
.btn:hover{background:#2980b9}
.btn-del{background:#e74c3c;color:white;padding:5px 10px;border:none;border-radius:4px;cursor:pointer;font-size:12px}
.btn-del:hover{background:#c0392b}
.res{padding:12px 15px;border-radius:6px;margin-top:12px;display:none;word-break:break-all;font-size:13px;line-height:1.6}
.ok{background:#e8f5e9;border-left:4px solid #27ae60}
.err{background:#ffebee;border-left:4px solid #e74c3c}
input[type=text]{width:100%;padding:9px;border:1px solid #ddd;border-radius:4px;font-size:14px;margin-bottom:8px}
input[type=file]{display:block;margin-bottom:8px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#2c3e50;color:white;padding:10px 12px;text-align:left}
td{padding:9px 12px;border-bottom:1px solid #eee;vertical-align:middle}
tr:hover{background:#f8f9fa}
.tx-link{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold;background:#e8f5e9;color:#27ae60;text-decoration:none}
.tx-pending{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;background:#fff3cd;color:#856404}
.mono{font-family:monospace;font-size:11px;color:#666}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-bottom:20px}
.sc{background:white;border-radius:8px;padding:15px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.08)}
.sn{font-size:28px;font-weight:bold;color:#3498db}
.sl{font-size:12px;color:#7f8c8d;margin-top:4px}
.info{background:#e8f4fd;border-left:4px solid #3498db;padding:10px 14px;border-radius:4px;font-size:13px;margin-top:10px}
</style>
</head>
<body>
<h1>DocChain</h1>
<p class="sub">Plateforme de gestion securisee de documents avec preuve d integrite blockchain - LegalVault</p>
<div class="stats">
  <div class="sc"><div class="sn" id="s1">-</div><div class="sl">Documents enregistres</div></div>
  <div class="sc"><div class="sn" id="s2">-</div><div class="sl">Ancres blockchain</div></div>
  <div class="sc"><div class="sn" id="s3">-</div><div class="sl">Ko stockes</div></div>
</div>
<div class="card">
  <h3>Deposer un document</h3>
  <input type="file" id="fi">
  <button class="btn" id="bu">Uploader et ancrer sur blockchain</button>
  <div class="res" id="ur"></div>
</div>
<div class="card">
  <h3>Verifier l integrite d un document</h3>
  <input type="text" id="hi" placeholder="Entrez le hash SHA-256 du document...">
  <button class="btn" id="bv">Verifier sur blockchain</button>
  <div class="res" id="vr"></div>
</div>
<div class="card">
  <h3>Historique des documents</h3>
  <button class="btn" id="br" style="margin-bottom:12px">Actualiser</button>
  <table>
    <thead><tr><th>Fichier</th><th>Hash SHA-256</th><th>Transaction</th><th>Date</th><th>Taille</th><th>Action</th></tr></thead>
    <tbody id="tb"><tr><td colspan="6" style="text-align:center;color:#999">Chargement...</td></tr></tbody>
  </table>
</div>
<script>
(function(){
  var autoRefreshTimer = null;

  function hasPending(docs){
    return docs.some(function(x){ return !x.tx_hash || x.tx_hash.length < 10; });
  }

  function startAutoRefresh(){
    if(autoRefreshTimer) return;
    autoRefreshTimer = setInterval(function(){
      fetch('/documents').then(function(r){return r.json();}).then(function(d){
        if(!hasPending(d.documents||[])){
          clearInterval(autoRefreshTimer);
          autoRefreshTimer = null;
        }
        renderDocs(d.documents||[]);
      });
    }, 5000);
  }

  function renderDocs(docs){
    var tb=document.getElementById('tb');
    if(!docs.length){
      tb.innerHTML='<tr><td colspan="6" style="text-align:center;color:#999">Aucun document</td></tr>';
      document.getElementById('s1').textContent='0';
      document.getElementById('s2').textContent='0';
      document.getElementById('s3').textContent='0';
      return;
    }
    document.getElementById('s1').textContent=docs.length;
    document.getElementById('s2').textContent=docs.filter(function(x){return x.tx_hash&&x.tx_hash.length>10;}).length;
    var tot=0;for(var i=0;i<docs.length;i++)tot+=(docs[i].file_size_bytes||0);
    document.getElementById('s3').textContent=Math.round(tot/1024);
    var rows='';
    for(var j=0;j<docs.length;j++){
      var x=docs[j];
      var h=x.hash_sha256||'';
      var tx=x.tx_hash||'';
      var dt=x.uploaded_at?new Date(x.uploaded_at).toLocaleString('fr-FR'):'-';
      var sz=x.file_size_bytes?Math.round(x.file_size_bytes/1024)+' Ko':'-';
      var txc=tx&&tx.length>10
        ?'<a class="tx-link" href="https://sepolia.etherscan.io/tx/'+tx+'" target="_blank">Voir TX</a>'
        :'<span class="tx-pending">En cours...</span>';
      var rk=x.RowKey||'';
      var fn=(x.filename||'').replace(/[\'\"<>]/g,'');
      rows+='<tr>'+
        '<td>'+(x.filename||'')+'</td>'+
        '<td class="mono">'+h.substring(0,16)+'...</td>'+
        '<td>'+txc+'</td>'+
        '<td>'+dt+'</td>'+
        '<td>'+sz+'</td>'+
        '<td><button class="btn-del" data-rk="'+rk+'" data-fn="'+fn+'">Supprimer</button></td>'+
        '</tr>';
    }
    tb.innerHTML=rows;
    var btns=tb.querySelectorAll('.btn-del');
    for(var k=0;k<btns.length;k++){
      btns[k].addEventListener('click',function(){
        var rk=this.getAttribute('data-rk');
        var fn=this.getAttribute('data-fn');
        if(!confirm('Supprimer '+fn+' ?'))return;
        fetch('/documents/'+rk,{method:'DELETE'}).then(function(r){return r.json();}).then(function(d){
          if(d.status==='deleted')ld();else alert('Erreur: '+d.error);
        });
      });
    }
  }

  function ld(){
    fetch('/documents').then(function(r){return r.json();}).then(function(d){
      renderDocs(d.documents||[]);
      if(hasPending(d.documents||[])) startAutoRefresh();
    }).catch(function(e){console.error(e);});
  }

  document.getElementById('bu').addEventListener('click',function(){
    var fi=document.getElementById('fi');
    if(!fi.files||!fi.files.length){alert('Choisissez un fichier');return;}
    var r=document.getElementById('ur');
    r.style.display='block';r.className='res ok';
    r.innerHTML='Upload en cours...';
    var fd=new FormData();fd.append('file',fi.files[0]);
    fetch('/upload',{method:'POST',body:fd}).then(function(res){return res.json();}).then(function(d){
      if(d.status==='uploaded'){
        r.className='res ok';
        r.innerHTML='<b>Document depose avec succes !</b><br><br>'+
          '<b>Fichier :</b> '+d.filename+'<br>'+
          '<b>Hash SHA-256 :</b> '+d.hash+'<br>'+
          '<b>Contrat :</b> '+d.blockchain+'<br>'+
          '<div class="info">Ancrage blockchain en cours... Le lien TX apparaitra automatiquement.</div>';
        ld();
        startAutoRefresh();
      }else{r.className='res err';r.innerHTML='<b>Erreur :</b> '+(d.error||JSON.stringify(d));}
    }).catch(function(e){r.className='res err';r.innerHTML='<b>Erreur reseau :</b> '+e.message;});
  });

  document.getElementById('bv').addEventListener('click',function(){
    var h=document.getElementById('hi').value.trim();
    if(!h){alert('Entrez un hash SHA-256');return;}
    var r=document.getElementById('vr');
    r.style.display='block';r.className='res';r.innerHTML='Verification en cours...';
    fetch('/verify/'+h).then(function(res){return res.json();}).then(function(d){
      if(d.exists){
        r.className='res ok';
        r.innerHTML='<b>Document authentifie !</b><br>'+
          '<b>Uploader :</b> '+d.uploader+'<br>'+
          '<b>Fichier :</b> '+d.filename+'<br>'+
          '<b>Date :</b> '+new Date(d.timestamp*1000).toLocaleString('fr-FR');
      }else{r.className='res err';r.innerHTML='<b>Document non trouve dans la blockchain</b>';}
    }).catch(function(e){r.className='res err';r.innerHTML='<b>Erreur :</b> '+e.message;});
  });

  document.getElementById('br').addEventListener('click',ld);
  ld();
  if(document.getElementById('tb').textContent.indexOf('En cours')>-1) startAutoRefresh();
})();
</script>
</body>
</html>"""


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/upload', methods=['POST'])
def upload():
    with LATENCY.time():
        if 'file' not in request.files:
            ERRORS.inc()
            return jsonify({'error': 'Aucun fichier'}), 400
        f         = request.files['file']
        content   = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
        file_size = len(content)
        try:
            client = BlobServiceClient.from_connection_string(CONN_STR)
            blob   = client.get_blob_client(container=CONTAINER, blob=f.filename)
            blob.upload_blob(content, overwrite=True)
            UPLOADS.inc()
        except Exception as e:
            ERRORS.inc()
            return jsonify({'error': f'Erreur Azure Storage: {str(e)}'}), 500
        # Sauvegarde immediate dans Table Storage
        row_key = str(uuid.uuid4())
        save_to_table(f.filename, file_hash, None, file_size, row_key)
        # Ancrage blockchain asynchrone - ne bloque pas la reponse
        if w3 and contract and PRIVATE_KEY:
            t = threading.Thread(
                target=register_on_blockchain_async,
                args=(file_hash, f.filename, row_key),
                daemon=True
            )
            t.start()
        return jsonify({
            'hash'      : file_hash,
            'filename'  : f.filename,
            'status'    : 'uploaded',
            'tx_hash'   : 'en cours...',
            'blockchain': CONTRACT_ADDRESS
        })


@app.route('/documents', methods=['GET'])
def list_documents():
    docs = get_all_documents()
    return jsonify({'documents': [dict(d) for d in docs], 'count': len(docs)})


@app.route('/verify/<file_hash>')
def verify(file_hash):
    try:
        result = contract.functions.verifyDocument(bytes.fromhex(file_hash)).call()
        return jsonify({
            'exists'   : result[0],
            'uploader' : result[1],
            'timestamp': result[2],
            'filename' : result[3]
        })
    except Exception as e:
        ERRORS.inc()
        return jsonify({'error': str(e)}), 500


@app.route('/documents/<row_key>', methods=['DELETE'])
def delete_document(row_key):
    if delete_from_table(row_key):
        return jsonify({'status': 'deleted', 'row_key': row_key})
    ERRORS.inc()
    return jsonify({'error': 'Suppression echouee'}), 500


@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/alert', methods=['POST'])
def alert():
    print(f"Alerte Grafana recue: {request.json}")
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)