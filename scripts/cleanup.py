import os, datetime, pytz
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

CONN_STR      = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER     = os.getenv('AZURE_CONTAINER_NAME', 'docchain')
RETENTION_DAYS = 30

def cleanup_old_blobs():
    print(f"[{datetime.datetime.now()}] 🧹 Démarrage du nettoyage (rétention : {RETENTION_DAYS} jours)")
    client    = BlobServiceClient.from_connection_string(CONN_STR)
    container = client.get_container_client(CONTAINER)
    blobs     = list(container.list_blobs())
    now       = datetime.datetime.now(pytz.utc)
    deleted   = 0
    kept      = 0

    for blob in blobs:
        age = (now - blob.last_modified).days
        if age > RETENTION_DAYS:
            container.delete_blob(blob.name)
            print(f"  🗑️  Supprimé : {blob.name} (âge : {age} jours)")
            deleted += 1
        else:
            print(f"  ✅ Conservé : {blob.name} (âge : {age} jours)")
            kept += 1

    print(f"[{datetime.datetime.now()}] Nettoyage terminé — {deleted} supprimé(s), {kept} conservé(s)")

if __name__ == '__main__':
    print("=== DocChain Cleanup ===")
    cleanup_old_blobs()