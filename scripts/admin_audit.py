"""
admin_audit.py — Audit FinOps et recommandations d'optimisation
Critère C23.1 — Script d'administration efficace
Critère C23.2 — Pertinence du choix technologique (Azure SDK Python)
"""
import os, datetime
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

CONN_STR  = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER = os.getenv('AZURE_CONTAINER_NAME', 'docchain')

def audit_storage_costs():
    print("=" * 60)
    print("AUDIT FINOPS — DocChain Storage Azure")
    print(f"Date : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)

    client    = BlobServiceClient.from_connection_string(CONN_STR)
    container = client.get_container_client(CONTAINER)
    blobs     = list(container.list_blobs())

    total_size_bytes = sum(b.size for b in blobs)
    total_size_mb    = total_size_bytes / (1024 * 1024)
    total_size_gb    = total_size_mb / 1024

    print(f"\n📊 INVENTAIRE DES RESSOURCES")
    print(f"   Nombre de fichiers : {len(blobs)}")
    print(f"   Taille totale      : {total_size_mb:.2f} Mo ({total_size_gb:.4f} Go)")
    print(f"   Coût estimé/mois   : {total_size_gb * 0.018:.4f} € (LRS West Europe @ 0.018€/Go)")

    now = datetime.datetime.now(datetime.timezone.utc)
    old_blobs = [b for b in blobs if (now - b.last_modified).days > 30]
    recent_blobs = [b for b in blobs if (now - b.last_modified).days <= 30]

    print(f"\n📅 ANALYSE PAR AGE")
    print(f"   Fichiers récents (< 30 jours) : {len(recent_blobs)}")
    print(f"   Fichiers anciens (> 30 jours) : {len(old_blobs)}")

    print(f"\n💡 RECOMMANDATIONS FINOPS")
    if old_blobs:
        old_size = sum(b.size for b in old_blobs) / (1024 * 1024)
        print(f"   ⚠️  {len(old_blobs)} fichier(s) de plus de 30 jours ({old_size:.2f} Mo)")
        print(f"   → Activer Azure Blob Lifecycle Management pour archivage automatique")
        print(f"   → Passer les fichiers > 90 jours en tier 'Cool' (économie ~50%)")
        print(f"   → Passer les fichiers > 365 jours en tier 'Archive' (économie ~90%)")
    else:
        print(f"   ✅ Tous les fichiers sont récents — pas d'optimisation immédiate nécessaire")

    print(f"\n🏗️  RECOMMANDATIONS ARCHITECTURE (CapEx → OpEx)")
    print(f"   1. Remplacer serveur dédié par Azure App Service F1 → 0€/mois")
    print(f"   2. Activer Auto-scaling pour absorber les pics (soldes, fêtes)")
    print(f"   3. Utiliser Azure CDN pour les assets statiques (-40% latence)")
    print(f"   4. Activer les métriques de coût Azure Cost Management")
    print(f"   5. Configurer des alertes budget à 80% du seuil mensuel")

    print(f"\n📈 OPTIMISATION SI — LEVIER CLOUD")
    print(f"   Modèle actuel    : CapEx (serveur dédié, coûts fixes)")
    print(f"   Modèle cible     : OpEx (Azure, paiement à l'usage)")
    print(f"   Économie estimée : 30-60% sur les coûts d'infrastructure")
    print(f"   Haute dispo      : SLA Azure App Service = 99.95%")
    print(f"   Élasticité       : Scale-out automatique en < 5 minutes")
    print("=" * 60)

if __name__ == '__main__':
    audit_storage_costs()