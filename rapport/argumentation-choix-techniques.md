# Argumentation des Choix Techniques — DocChain
**Étudiant** : Sina Ramezani | EFREI Paris | 2025-2026

---

## Pourquoi Microsoft Azure ? (C21)

**Problème de départ :** WebMarket+ souffre de pics de charge lors des soldes 
et fêtes, d'une visibilité nulle sur les coûts, et d'une dépendance forte à 
une équipe IT interne.

**Choix : Azure for Students**
- **Gratuit** : 100$ de crédit sans carte bancaire via l'email EFREI
- **Leader du marché** : Azure est le 2ème cloud mondial, utilisé par 95% 
  des entreprises du Fortune 500
- **Région West Europe** : données hébergées en Europe, conformité RGPD garantie
- **SLA 99.95%** sur App Service = moins de 4h d'indisponibilité par an

**Pourquoi pas AWS ?** AWS demande une CB pour le Free Tier. Azure for Students 
est gratuit avec l'email académique — choix pragmatique et économique.

**Pourquoi pas Google Cloud ?** L'écosystème Azure est le plus intégré avec 
les outils Microsoft (Active Directory, Office 365) qu'utilisent la plupart 
des PME comme WebMarket+.

---

## Pourquoi Azure Blob Storage ? (C21.1)

**Service choisi :** Azure Blob Storage (container `docchain`, accès privé)

**Amélioration concrète par rapport au serveur dédié :**
| Avant (serveur dédié) | Après (Azure Blob Storage) |
|---|---|
| Stockage limité au disque local | Capacité illimitée |
| Pas de redondance | 3 copies automatiques (LRS) |
| Accès uniquement local | Accès mondial via HTTPS |
| Pas de chiffrement | AES-256 au repos automatique |
| Backup manuel | Soft delete 7 jours intégré |

**Intégration dans le code :** SDK officiel `azure-storage-blob` en Python, 
5 lignes de code pour uploader un fichier vers le cloud.

---

## Pourquoi Azure Key Vault ? (C21.1 + C25)

**Problème :** les clés d'accès Azure Storage dans un fichier `.env` local 
constituent un risque de sécurité — si le fichier est partagé par erreur, 
les données sont compromises.

**Solution : Azure Key Vault `docchain-kv-sina`**
- Stockage centralisé et chiffré de tous les secrets
- Accès contrôlé par des politiques IAM strictes
- Audit de chaque accès (qui a lu quel secret, quand)
- Rotation automatique des secrets possible
- URI du coffre : `https://docchain-kv-sina.vault.azure.net/`

**Justification professionnelle :** c'est la pratique standard en entreprise. 
Aucun secret ne doit jamais être dans le code ou dans un fichier versionné.

---

## Pourquoi Terraform ? (C22)

**Alternatives considérées :**
- Azure CLI : scripts bash fragiles, pas reproductibles
- ARM Templates : syntaxe JSON verbeuse, uniquement Azure
- Pulumi : moins mature, moins de documentation

**Choix : Terraform v1.14**
- **Déclaratif** : on décrit l'état voulu, Terraform trouve le chemin
- **Multi-cloud** : le même outil fonctionnerait sur AWS ou GCP
- **Idempotent** : relancer `terraform apply` ne crée pas de doublons
- **Versionnable** : l'infrastructure est du code, auditée dans Git
- **Preuve :** `terraform apply` → `No changes` = infrastructure stable

**Résultat :** 7 ressources Azure créées en 3 minutes, reproductibles à 
l'identique par n'importe quel membre de l'équipe.

---

## Pourquoi Python pour les scripts admin ? (C23)

**Choix : Python 3.11 + azure-storage-blob SDK**

**Justification :**
- SDK Azure officiel `azure-storage-blob` : maintenu par Microsoft, 
  documenté, testé
- Lisibilité : code compréhensible par toute l'équipe, pas seulement DevOps
- Logs horodatés : chaque action est tracée avec timestamp précis
- Gestion d'erreurs : try/except sur chaque opération, exit codes 0/1
- Planification : compatible avec Azure Functions Timer Trigger en production

**3 scripts produits :**
- `health_check.py` : vérifie la santé des services toutes les 5 min
- `cleanup.py` : supprime les fichiers > 30 jours (conformité RGPD)
- `rotate_secrets.py` : vérifie et simule la rotation des clés (90 jours)
- `admin_audit.py` : audit FinOps et recommandations d'optimisation

---

## Pourquoi Grafana Cloud + Prometheus ? (C24)

**Alternatives considérées :**
- Azure Application Insights : payant au-delà du Free Tier
- Azure Monitor : moins de flexibilité pour les dashboards custom
- Datadog : payant

**Choix : Grafana Cloud (plan gratuit) + prometheus_client Python**

**Métriques choisies et leur justification :**

| Métrique | Pourquoi pertinente |
|---|---|
| `docchain_uploads_total` | Mesure l'activité principale — une chute à 0 = problème |
| `docchain_errors_total` | Détection immédiate des dysfonctionnements |
| `docchain_request_duration_seconds` | Identifie les ralentissements (p95, p99) |

**Alerte configurée :** si `docchain_errors_total > 0` pendant 2 minutes 
→ notification webhook. Justification : dans une app de gestion de documents, 
toute erreur persistante est anormale et doit être traitée immédiatement.

---

## Pourquoi Ethereum Sepolia + Solidity ? (C26)

**Problème métier :** WebMarket+ a besoin de prouver l'intégrité de ses 
documents (contrats fournisseurs, factures). Un fichier peut être falsifié 
sans laisser de trace sur un serveur classique.

**Solution blockchain :**
La blockchain est immuable par nature. Une fois qu'un hash est enregistré, 
il est impossible de le modifier ou supprimer. C'est une preuve cryptographique.

**Choix : Ethereum Sepolia (testnet)**
- Réseau de test public, ETH gratuit via faucet
- Même comportement qu'Ethereum mainnet
- Smart contract déployé à : `0xE1A55786068869B9318811f61931783600fc8FCf`
- Vérifiable publiquement sur Sepolia Etherscan

**Choix : Solidity + web3.py**
- Solidity : langage standard pour les smart contracts Ethereum
- web3.py : SDK Python officiel pour interagir avec Ethereum
- Alchemy : provider gratuit (300M requêtes/mois)

**Flux complet prouvé :**
1. Upload fichier → Flask calcule SHA-256
2. `registerDocument(hash, filename)` → transaction signée envoyée
3. Transaction confirmée → `tx_hash` retourné à l'utilisateur
4. `verifyDocument(hash)` → vérifie l'intégrité à tout moment

**Preuve :** transaction visible sur Etherscan avec uploader, timestamp, 
et nom du fichier — falsification impossible.

---

## Pourquoi HTTPS + TLS 1.2 ? (C25)

**Conformité RGPD :** le RGPD impose la protection des données en transit.
**Solution déployée :** `https_only = true` dans Terraform sur l'App Service.
**TLS minimum 1.2 :** exclut les protocoles vulnérables (SSL 3.0, TLS 1.0).
**Résultat :** toute tentative HTTP est redirigée automatiquement vers HTTPS.

---

## Résumé des choix — tableau de décision

| Composant | Choix retenu | Alternative écartée | Raison |
|---|---|---|---|
| Cloud | Azure | AWS, GCP | Gratuit avec email EFREI |
| Stockage | Blob Storage | S3, GCS | Même cloud, SDK natif |
| Secrets | Key Vault | .env local | Sécurité professionnelle |
| IaC | Terraform | ARM Templates | Multi-cloud, déclaratif |
| Monitoring | Grafana Cloud | Datadog, Insights | Gratuit, flexible |
| Blockchain | Ethereum Sepolia | Hyperledger, BSC | Standard, testnet gratuit |
| Langage | Python | Node.js, Java | SDK Azure natif, lisible |
| CI/CD | GitHub Actions | Jenkins, CircleCI | Intégré à GitHub, gratuit |