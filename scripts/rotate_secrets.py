import os, datetime
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

CONN_STR = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
ACCOUNT  = os.getenv('AZURE_STORAGE_ACCOUNT')

def check_key_age():
    print(f"[{datetime.datetime.now()}] 🔑 Vérification des clés d'accès Storage")
    try:
        client = BlobServiceClient.from_connection_string(CONN_STR)
        props  = client.get_service_properties()
        print(f"[{datetime.datetime.now()}] ✅ Clé active valide — compte : {ACCOUNT}")
        print(f"[{datetime.datetime.now()}] ℹ️  Recommandation : rotation des clés tous les 90 jours")
        print(f"[{datetime.datetime.now()}] ℹ️  Pour rotation manuelle : az storage account keys renew")
        return True
    except Exception as e:
        print(f"[{datetime.datetime.now()}] ❌ Clé invalide ou expirée — {e}")
        return False

def simulate_rotation():
    print(f"[{datetime.datetime.now()}] 🔄 Simulation de rotation de clé")
    print(f"[{datetime.datetime.now()}] 1. Génération nouvelle clé secondaire...")
    print(f"[{datetime.datetime.now()}] 2. Mise à jour des variables d'environnement...")
    print(f"[{datetime.datetime.now()}] 3. Validation de la nouvelle clé...")
    print(f"[{datetime.datetime.now()}] ✅ Rotation simulée avec succès")
    print(f"[{datetime.datetime.now()}] ℹ️  En production : az storage account keys renew --account-name {ACCOUNT} --key primary")

if __name__ == '__main__':
    print("=== DocChain Rotate Secrets ===")
    check_key_age()
    simulate_rotation()