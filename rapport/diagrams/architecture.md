# Schémas d'architecture DocChain

## 1. Architecture Cloud Globale (C21)

```mermaid
graph TB
    User[Utilisateur] -->|HTTPS| App[Azure App Service\ndocchain-sina-efrei]
    App -->|azure-storage-blob SDK| Storage[Azure Blob Storage\ndocchainsinara]
    App -->|web3.py| Blockchain[Ethereum Sepolia\nSmart Contract]
    App -->|prometheus_client| Metrics[/metrics endpoint]
    Metrics -->|scrape 1min| Grafana[Grafana Cloud\ndocchain.grafana.net]
    Grafana -->|alerte webhook| App
    Storage -->|chiffrement AES-256| Data[(Fichiers stockés)]
    KV[Azure Key Vault\ndocchain-kv-sina] -->|secrets| App
    Terraform[Terraform IaC] -->|provision| App
    Terraform -->|provision| Storage
    Terraform -->|provision| KV
    style App fill:#0078D4,color:#fff
    style Storage fill:#0078D4,color:#fff
    style KV fill:#0078D4,color:#fff
    style Blockchain fill:#627EEA,color:#fff
    style Grafana fill:#F46800,color:#fff
```

## 2. Pipeline CI/CD (C22)

```mermaid
graph LR
    Dev[Développeur] -->|git push| GitHub[GitHub\ndocchain-cloud]
    GitHub -->|trigger| Actions[GitHub Actions]
    Actions --> Test[Job: Tests Python]
    Actions --> TF[Job: Terraform Validate]
    Actions --> Docker[Job: Build Docker]
    Test -->|OK| Deploy[Déploiement Azure]
    TF -->|OK| Deploy
    Docker -->|OK| Deploy
    Deploy --> Azure[Azure App Service\nProduction]
    style GitHub fill:#24292e,color:#fff
    style Actions fill:#2088FF,color:#fff
    style Azure fill:#0078D4,color:#fff
```

## 3. Séquence Blockchain (C26)

```mermaid
sequenceDiagram
    actor User as Utilisateur
    participant Flask as App Flask
    participant Azure as Azure Blob Storage
    participant Web3 as web3.py
    participant SC as Smart Contract\nSepolia
    participant ES as Etherscan

    User->>Flask: POST /upload (fichier)
    Flask->>Flask: Calcul SHA-256
    Flask->>Azure: upload_blob(fichier)
    Azure-->>Flask: ✅ Stocké
    Flask->>Web3: registerDocument(hash, filename)
    Web3->>SC: Transaction signée
    SC->>SC: Vérification unicité
    SC-->>Web3: Event DocumentRegistered
    Web3-->>Flask: tx_hash
    Flask-->>User: {hash, tx_hash, blockchain}
    User->>ES: Vérifier sur Etherscan
    ES-->>User: Transaction confirmée ✅
```

## 4. Matrice de Responsabilité Partagée (C25)

```mermaid
graph TB
    subgraph WebMarketPlus["WebMarket+ (Responsabilité Client)"]
        A[Code applicatif]
        B[Données utilisateurs]
        C[Configuration IAM]
        D[Gestion des secrets .env]
        E[Smart contract Solidity]
    end
    subgraph Azure["Microsoft Azure (Responsabilité Fournisseur)"]
        F[Infrastructure physique]
        G[Hyperviseur]
        H[Réseau physique]
        I[Chiffrement AES-256 Storage]
        J[SLA 99.95% App Service]
        K[Patches OS]
    end
    WebMarketPlus -->|PaaS Model| Azure
```