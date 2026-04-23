# DocChain — Gestionnaire de documents cloud avec preuve blockchain

**Étudiant** : Sina Ramezani  
**École** : EFREI Paris | Promotion 2025-2026  
**Matière** : Panorama du Cloud — BC04  

---

## Présentation du projet

DocChain est une application web permettant d'uploader des fichiers de manière sécurisée sur le cloud Azure. Chaque fichier uploadé est identifié par son empreinte SHA-256, enregistrée sur la blockchain Ethereum pour garantir son intégrité. L'infrastructure est entièrement provisionnée par Terraform et surveillée en temps réel par Grafana Cloud.

**URL de l'application** : https://docchain-sina-efrei.azurewebsites.net

---

## Architecture

Utilisateur → Flask (Azure App Service)
↓
Azure Blob Storage (stockage fichiers)
↓
Hash SHA-256 → Smart Contract Ethereum Sepolia
↓
Métriques → Grafana Cloud (monitoring)

---

## Compétences validées

| Compétence | Description | Implémentation |
|---|---|---|
| C21 | Intégration services cloud | Azure Blob Storage via SDK `azure-storage-blob` |
| C22 | Infrastructure as Code | Terraform — 5 ressources Azure provisionnées |
| C23 | Scripts d'administration | 3 scripts Python (health check, cleanup, rotation secrets) |
| C24 | Monitoring | Grafana Cloud + Prometheus + alertes |
| C25 | Sécurité | HTTPS, chiffrement AES-256, IAM, RGPD |
| C26 | Blockchain | Smart contract Solidity sur Ethereum Sepolia |

---

## Stack technologique

| Technologie | Rôle | Gratuit |
|---|---|---|
| Microsoft Azure | Cloud provider | ✅ Azure for Students |
| Python / Flask | Application web | ✅ |
| Terraform | Infrastructure as Code | ✅ |
| Azure Blob Storage | Stockage des fichiers | ✅ |
| Azure App Service | Hébergement de l'app | ✅ |
| Grafana Cloud | Monitoring et alertes | ✅ |
| Solidity / Ethereum Sepolia | Blockchain | ✅ |
| GitHub Actions | CI/CD | ✅ |

---

## Structure du projet

docchain-cloud/
├── app/                    # Application Flask
│   └── app.py              # Routes, upload, métriques, blockchain
├── infra/                  # Infrastructure Terraform
│   ├── main.tf             # Ressources Azure
│   ├── variables.tf        # Variables
│   ├── outputs.tf          # Outputs (URL, connection string)
│   └── README.md           # Documentation IaC
├── scripts/                # Scripts d'administration
│   ├── health_check.py     # Vérification santé des services
│   ├── cleanup.py          # Nettoyage fichiers > 30 jours
│   ├── rotate_secrets.py   # Rotation des clés d'accès
│   ├── generate_traffic.py # Génération de trafic pour tests
│   └── README.md           # Documentation scripts
├── monitoring/             # Configuration monitoring
│   ├── prometheus.yml      # Config scrape Prometheus
│   └── README.md           # Documentation monitoring
├── blockchain/             # Smart contract
│   └── DocumentRegistry.sol # Contrat Solidity
├── rapport/                # Rapport de sécurisation
│   └── rapport-securisation.md
├── .env                    # Variables d'environnement (non commité)
├── .gitignore              # Fichiers exclus du repo
└── requirements.txt        # Dépendances Python

---

## Lancer le projet en local

### Prérequis
- Python 3.11+
- Terraform
- Azure CLI
- Compte Azure for Students

### Installation

```bash
# Cloner le repo
git clone https://github.com/Behsouu/docchain-cloud.git
cd docchain-cloud

# Créer l'environnement Python
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Remplir les valeurs dans .env
```

### Déployer l'infrastructure Azure

```bash
cd infra
terraform init
terraform plan
terraform apply
```

### Lancer l'application

```bash
cd app
python app.py
```

L'application est accessible sur http://127.0.0.1:5000

---

## Infrastructure Azure (Terraform)

5 ressources créées automatiquement :

| Ressource | Nom | Rôle |
|---|---|---|
| Resource Group | docchain-rg | Conteneur de toutes les ressources |
| Storage Account | docchainsinara | Stockage des fichiers |
| Storage Container | docchain | Dossier privé dans le Storage |
| App Service Plan | docchain-plan | Plan d'hébergement (F1 gratuit) |
| Linux Web App | docchain-sina-efrei | Application Flask déployée |

---

## Smart Contract Blockchain

- **Réseau** : Ethereum Sepolia (testnet)
- **Adresse** : `0xE1A55786068869B9318811f61931783600fc8FCf`
- **Vérifiable sur** : https://sepolia.etherscan.io/address/0xE1A55786068869B9318811f61931783600fc8FCf

### Fonctions du contrat

```solidity
// Enregistrer l'empreinte d'un document
registerDocument(bytes32 hash, string filename)

// Vérifier si un document existe
verifyDocument(bytes32 hash) returns (bool, address, uint256, string)

// Nombre total de documents enregistrés
getDocumentCount() returns (uint256)
```

---

## Monitoring

- **Dashboard Grafana** : https://docchain.grafana.net
- **Métriques exposées** : `/metrics` (format Prometheus)
- **Alerte configurée** : taux d'erreur > 0 pendant 2 minutes

---

## Rapport de sécurisation

Le rapport complet est disponible dans [`rapport/rapport-securisation.md`](rapport/rapport-securisation.md).

Il couvre :
- Gestion des identités et des accès (IAM)
- Chiffrement au repos et en transit
- Conformité RGPD
- Monitoring et détection des incidents
- Sécurité blockchain
- Tableau de synthèse de toutes les mesures

