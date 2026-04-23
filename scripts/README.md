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