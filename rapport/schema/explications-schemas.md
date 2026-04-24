# Explications des Schémas d'Architecture — DocChain
**Étudiant** : Sina Ramezani | EFREI Paris | 2025-2026

---

## Schéma 1 — Architecture Cloud Globale Azure (C21)

Ce schéma illustre l'intégration de trois services Azure distincts : App Service 
pour l'hébergement de l'application Flask, Blob Storage pour le stockage sécurisé 
des fichiers uploadés par les commerçants, et Key Vault pour la gestion centralisée 
des secrets. Chaque service communique via les SDK officiels Azure, ce qui améliore 
concrètement les fonctionnalités de WebMarket+ par rapport à l'hébergement sur 
serveur dédié. L'ensemble est déployé en région West Europe, garantissant la 
conformité RGPD pour les données des commerçants. La connexion blockchain via 
web3.py permet d'ancrer chaque document sur Ethereum Sepolia, ajoutant une couche 
de traçabilité immuable.

**Critères validés : C21.1, C21.2, C25.1**

---

## Schéma 2 — Infrastructure as Code Terraform (C22)

Ce schéma représente le cycle de vie complet d'une infrastructure définie en code 
avec Terraform. Le workflow init → plan → apply garantit des déploiements 
reproductibles et sans intervention manuelle sur la console Azure. Le fichier d'état 
(tfstate) est la pierre angulaire de la gestion d'état : il permet à Terraform de 
comparer l'état réel de l'infrastructure avec la configuration souhaitée, et de 
n'appliquer que les différences nécessaires. La preuve concrète de reproductibilité 
est le résultat `No changes` obtenu lors d'un second `terraform apply`, attestant 
que l'infrastructure correspond exactement au code versionné sur GitHub.

**Critères validés : C22.1, C22.2**

---

## Schéma 3 — Pipeline CI/CD Docker et GitHub Actions (C21.2 + C22)

Ce schéma illustre le pipeline d'intégration et de déploiement continu mis en place 
avec GitHub Actions. À chaque push sur la branche principale, trois jobs s'exécutent 
en parallèle : les tests Python vérifient que le code s'importe sans erreur, 
Terraform validate s'assure que l'infrastructure as code est syntaxiquement correcte, 
et le build Docker construit une image multi-stage optimisée. Le Dockerfile multi-stage 
sépare la phase de build (installation des dépendances) de la phase de production 
(image légère), réduisant la taille finale de l'image et la surface d'attaque. 
Ce processus automatisé élimine les erreurs manuelles et accélère les déploiements, 
répondant directement au critère C21.2 sur l'automatisation des processus.

**Critères validés : C21.2, C22.2**

---

## Schéma 4 — Séquence Blockchain Preuve d'intégrité (C26)

Ce diagramme de séquence détaille le flux complet de la preuve d'intégrité blockchain 
implémentée dans DocChain. Chaque document uploadé est identifié par son empreinte 
SHA-256 unique, calculée côté serveur par Flask avant tout stockage. Cette empreinte 
est ensuite ancrée de manière immuable dans le smart contract DocumentRegistry.sol 
déployé sur Ethereum Sepolia. La transaction blockchain retourne un identifiant unique 
(tx_hash) vérifiable publiquement sur Sepolia Etherscan, constituant une preuve 
cryptographique infalsifiable. Si un fichier est modifié après upload, son hash ne 
correspondra plus à celui enregistré sur la blockchain, rendant toute falsification 
immédiatement détectable. La fonction verifyDocument permet de vérifier l'intégrité 
à tout moment sans interaction humaine.

**Critères validés : C26.1, C26.2**

---

## Schéma 5 — Modèle de Responsabilité Partagée PaaS (C25)

Ce schéma clarifie la répartition des responsabilités entre Microsoft Azure et 
WebMarket+ dans le cadre d'une architecture PaaS. Azure prend en charge toutes 
les couches basses de l'infrastructure : physique, réseau, hyperviseur, système 
d'exploitation, runtime et chiffrement au repos AES-256, avec un SLA de 99,95% 
garantissant la haute disponibilité. WebMarket+ reste entièrement responsable de 
ce qui lui appartient : ses données métier, son code applicatif Flask, sa 
configuration IAM selon le principe du moindre privilège, ses secrets dans Key Vault 
avec rotation recommandée tous les 90 jours, et son smart contract Solidity. 
La zone de responsabilité partagée couvre le chiffrement en transit (Azure fournit 
TLS, WebMarket+ active HTTPS only), le contrôle réseau et la journalisation. 
Ce modèle permet à WebMarket+ de concentrer ses ressources sur la valeur métier 
plutôt que sur l'exploitation technique.

**Critères validés : C25.1, C25.2**

---

## Résumé de couverture des critères

| Schéma | Critères RNCP couverts |
|--------|----------------------|
| 1 — Architecture Cloud Globale | C21.1, C21.2, C25.1 |
| 2 — Infrastructure as Code Terraform | C22.1, C22.2 |
| 3 — Pipeline CI/CD Docker | C21.2, C22.2 |
| 4 — Séquence Blockchain | C26.1, C26.2 |
| 5 — Responsabilité Partagée | C25.1, C25.2 |
| **Couverture totale** | **C21 à C26 — 100%** |