import os, sys, datetime
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

CONN_STR  = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER = os.getenv('AZURE_CONTAINER_NAME', 'docchain')

def check_storage():
    try:
        client = BlobServiceClient.from_connection_string(CONN_STR)
        container = client.get_container_client(CONTAINER)
        container.get_container_properties()
        print(f"[{datetime.datetime.now()}] ✅ Storage Azure : OK — container '{CONTAINER}' accessible")
        return True
    except Exception as e:
        print(f"[{datetime.datetime.now()}] ❌ Storage Azure : ERREUR — {e}")
        return False

def check_blob_count():
    try:
        client = BlobServiceClient.from_connection_string(CONN_STR)
        container = client.get_container_client(CONTAINER)
        blobs = list(container.list_blobs())
        print(f"[{datetime.datetime.now()}] 📁 Nombre de fichiers dans le storage : {len(blobs)}")
        return len(blobs)
    except Exception as e:
        print(f"[{datetime.datetime.now()}] ❌ Impossible de lister les blobs — {e}")
        return -1

if __name__ == '__main__':
    print("=== DocChain Health Check ===")
    storage_ok = check_storage()
    blob_count  = check_blob_count()
    print("=== Résultat ===")
    if storage_ok:
        print("✅ Tous les services sont opérationnels")
        sys.exit(0)
    else:
        print("❌ Des services sont en erreur")
        sys.exit(1)