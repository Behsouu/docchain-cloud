# Scripts d'administration DocChain

## Pourquoi Python ?
- SDK Azure natif (azure-storage-blob) : interaction directe avec Azure sans passer par l'interface web
- Lisible et maintenable : syntaxe claire, idéale pour des scripts d'administration
- Logs horodatés : chaque action est tracée avec un timestamp précis
- Gestion d'erreurs : try/except sur chaque opération critique

## Pourquoi Azure Blob Storage ?
- Scalable : stockage illimité, paiement à l'usage
- Sécurisé : chiffrement au repos activé par défaut (AES-256)
- Intégré : SDK Python officiel maintenu par Microsoft
- Gratuit : 5 Go inclus dans Azure for Students

## Scripts disponibles

### health_check.py
Vérifie que le Storage Azure et le container docchain sont accessibles.
Lance une alerte si un service est indisponible.


python scripts/health_check.py

### cleanup.py
Supprime automatiquement les fichiers de plus de 30 jours.
Permet de gérer les coûts de stockage et respecter la politique de rétention RGPD.
python scripts/cleanup.py

### rotate_secrets.py
Vérifie la validité des clés d'accès et simule leur rotation.
En production : rotation automatique tous les 90 jours via Azure Key Vault.
python scripts/rotate_secrets.py

## Planification automatique
En production, ces scripts sont déclenchés automatiquement via Azure Functions Timer Trigger :
- health_check.py : toutes les 5 minutes
- cleanup.py : tous les jours à minuit
- rotate_secrets.py : tous les 90 jours