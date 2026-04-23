# Rapport de Sécurisation — Application DocChain
---
**Étudiant** : Sina Ramezani  
**École** : EFREI Paris  
**Promotion** : 2025-2026  
**Matière** : Panorama du Cloud — BC04  
**Date** : Avril 2026  

---

## Introduction

Ce rapport présente l'ensemble des mesures de sécurité mises en place dans le cadre du projet DocChain, une application web de gestion de documents déployée sur Microsoft Azure. L'objectif de ce document est de démontrer que chaque décision technique a été prise en tenant compte des enjeux de sécurité, de conformité réglementaire et de protection des données utilisateurs.

DocChain permet à un utilisateur d'uploader des fichiers qui sont stockés dans Azure Blob Storage. Chaque fichier est identifié par son empreinte numérique (hash SHA-256), qui est vérifiable à tout moment via un smart contract déployé sur la blockchain Ethereum. L'ensemble de l'infrastructure est provisionnée via Terraform (Infrastructure as Code) et surveillée en temps réel par Grafana Cloud.

---

## 1. Architecture générale de l'application

### 1.1 Vue d'ensemble

L'application DocChain est composée des éléments suivants :

- **Frontend + Backend** : Application Flask (Python) hébergée sur Azure App Service
- **Stockage** : Azure Blob Storage (container privé `docchain`)
- **Infrastructure** : Provisionnée par Terraform, versionnée sur GitHub
- **Blockchain** : Smart contract Solidity déployé sur Ethereum Sepolia
- **Monitoring** : Grafana Cloud avec métriques Prometheus
- **Administration** : Scripts Python automatisés (health check, nettoyage, rotation des secrets)

### 1.2 Flux de données

Voici ce qui se passe concrètement quand un utilisateur uploade un fichier :

1. L'utilisateur envoie son fichier via HTTPS (connexion chiffrée)
2. Flask reçoit le fichier et calcule son empreinte SHA-256
3. Le fichier est stocké dans Azure Blob Storage (chiffré au repos)
4. L'empreinte est vérifiée via le smart contract blockchain
5. Les métriques de l'opération sont enregistrées dans Prometheus
6. Grafana surveille ces métriques et déclenche une alerte si nécessaire

### 1.3 Pourquoi ces choix technologiques ?

**Azure** a été choisi car il propose un programme Azure for Students offrant 100$ de crédit gratuit sans carte bancaire, ce qui est particulièrement adapté au contexte académique. De plus, Azure est l'un des trois leaders mondiaux du cloud (avec AWS et GCP) et est massivement utilisé en entreprise.

**Python / Flask** a été choisi pour sa simplicité, sa lisibilité, et surtout pour la richesse de son écosystème cloud : le SDK `azure-storage-blob` permet d'interagir directement avec Azure Storage en quelques lignes de code.

**Terraform** a été retenu plutôt qu'Azure CLI ou ARM Templates car il est multi-cloud, déclaratif, et dispose d'une communauté très large. Il permet de versionner l'infrastructure comme du code, ce qui facilite la reproductibilité et l'audit.

---

## 2. Sécurité des accès et des identités (IAM)

### 2.1 Principe du moindre privilège

Le principe du moindre privilège est une règle fondamentale en sécurité informatique : chaque composant ou utilisateur ne doit avoir accès qu'aux ressources strictement nécessaires à son fonctionnement. Si un composant est compromis, les dégâts sont ainsi limités.

Dans DocChain, ce principe est appliqué de la manière suivante :

| Composant | Ce à quoi il a accès | Ce à quoi il n'a PAS accès |
|-----------|---------------------|---------------------------|
| Application Flask | Lecture et écriture dans le container Blob `docchain` | Autres containers, clés IAM, configuration réseau |
| Terraform | Création et gestion des ressources dans `docchain-rg` | Autres Resource Groups, abonnements |
| Scripts admin | Listage et suppression de blobs dans `docchain` | Modification de la configuration Azure |
| Grafana Cloud | Lecture des métriques Prometheus | Accès au code ou aux données |

### 2.2 Gestion de l'identité Azure

Un compte Azure for Students a été utilisé sous le tenant EFREI (`efrei.net`). L'identifiant de l'abonnement est `f009ab00-8a04-4b17-8ca9-60ef8e8e92c1`. Toutes les ressources sont regroupées dans le Resource Group `docchain-rg`, ce qui facilite la gestion des droits et permet de supprimer l'ensemble des ressources en une seule opération si nécessaire.

### 2.3 Protection des clés d'accès

Les clés d'accès au Storage Account sont des informations sensibles. Elles permettent à quiconque les possède de lire, écrire ou supprimer n'importe quel fichier dans le stockage. Plusieurs mesures ont été prises pour les protéger :

**Aucune clé dans le code source** : toutes les clés sont stockées dans un fichier `.env` local, jamais commité sur GitHub. Le fichier `.gitignore` exclut explicitement `.env` ainsi que les fichiers d'état Terraform (`.tfstate`) qui peuvent contenir des informations sensibles.

**Variables d'environnement sur Azure** : lorsque l'application est déployée sur App Service, les clés sont injectées via les variables d'environnement Azure, accessibles uniquement aux personnes ayant les droits d'administration sur la ressource.

**Rotation recommandée** : le script `rotate_secrets.py` rappelle la bonne pratique de rotation des clés tous les 90 jours et indique la commande Azure CLI pour le faire. En production, cette rotation serait automatisée via Azure Key Vault.

---

## 3. Chiffrement des données

### 3.1 Chiffrement en transit (données qui voyagent)

Toutes les communications entre l'utilisateur et l'application sont chiffrées via HTTPS (TLS). Concrètement :

- **HTTPS uniquement** a été activé sur l'App Service `docchain-sina-efrei`. Toute tentative de connexion en HTTP est automatiquement redirigée vers HTTPS.
- La **version TLS minimale est 1.2**, ce qui exclut les protocoles anciens et vulnérables (SSL 3.0, TLS 1.0, TLS 1.1).
- Les communications entre l'application Flask et Azure Storage passent par les endpoints HTTPS officiels d'Azure (`docchainsinara.blob.core.windows.net`).

### 3.2 Chiffrement au repos (données stockées)

Azure Storage Service Encryption (SSE) est activé par défaut sur le Storage Account `docchainsinara`. Cela signifie que chaque fichier est automatiquement chiffré avec l'algorithme AES-256 avant d'être écrit sur les disques de Microsoft, et déchiffré automatiquement lors de la lecture. Ce chiffrement est transparent pour l'application.

Le type de chiffrement utilisé est **Clés gérées par Microsoft**, ce qui signifie que Microsoft gère le cycle de vie des clés de chiffrement dans ses propres systèmes sécurisés. Pour un niveau de sécurité encore plus élevé (non requis dans ce projet), on pourrait utiliser des clés gérées par le client via Azure Key Vault.

### 3.3 Intégrité des données via blockchain

En complément du chiffrement, l'intégrité de chaque fichier est garantie par la blockchain. Voici comment :

1. Avant l'upload, l'application calcule l'empreinte SHA-256 du fichier
2. Cette empreinte (64 caractères hexadécimaux) est unique : deux fichiers différents produisent toujours des empreintes différentes
3. L'empreinte est vérifiable à tout moment via la fonction `verifyDocument()` du smart contract

Si quelqu'un modifie un fichier après son upload, son empreinte SHA-256 changera et ne correspondra plus à ce qui est enregistré dans la blockchain. La falsification devient ainsi détectable et prouvable.

---

## 4. Sécurité de l'infrastructure

### 4.1 Infrastructure as Code (Terraform)

L'ensemble de l'infrastructure Azure est définie dans des fichiers Terraform versionnés sur GitHub. Cette approche présente plusieurs avantages en termes de sécurité :

- **Auditabilité** : chaque modification de l'infrastructure est tracée dans l'historique Git avec un message de commit explicatif
- **Reproductibilité** : l'infrastructure peut être recrée à l'identique en cas d'incident
- **Revue de code** : les modifications d'infrastructure peuvent être revues par des pairs avant d'être appliquées
- **Pas de configuration manuelle** : les erreurs humaines liées aux clics dans la console Azure sont évitées

Les fichiers Terraform sensibles (`.tfstate`, `terraform.tfvars`) sont exclus du dépôt Git via `.gitignore`. Le fichier d'état Terraform contient en effet des valeurs sensibles comme les chaînes de connexion.

### 4.2 Réseau et accès

**Container Blob privé** : le container `docchain` est configuré en accès privé. Cela signifie qu'aucun fichier n'est accessible publiquement via une URL directe. L'accès est uniquement possible via l'application Flask authentifiée avec la clé d'accès.

**Pas de ports inutiles ouverts** : l'App Service n'expose que le port 443 (HTTPS). Le port 22 (SSH) est désactivé par défaut sur les App Services Azure en mode Linux.

### 4.3 Séparation des environnements

Toutes les ressources sont regroupées dans le Resource Group `docchain-rg` avec les tags suivants :
- `projet : docchain`
- `etudiant : efrei`
- `environnement : dev`

Cette organisation permet de clairement identifier les ressources et de les distinguer d'éventuelles ressources de production futures.

---

## 5. Monitoring et détection des incidents

### 5.1 Pourquoi le monitoring est une mesure de sécurité

Le monitoring ne sert pas uniquement à surveiller les performances. C'est aussi un outil de sécurité essentiel : une augmentation soudaine des erreurs peut indiquer une tentative d'attaque (injection, déni de service), une fuite de données, ou un dysfonctionnement critique.

### 5.2 Métriques surveillées

L'application expose ses métriques en temps réel sur l'endpoint `/metrics` au format Prometheus. Trois métriques principales sont surveillées :

**docchain_uploads_total** (Counter) : compte le nombre total de fichiers uploadés depuis le démarrage de l'application. Une chute soudaine à zéro peut indiquer un problème avec Azure Storage ou un blocage de l'application.

**docchain_errors_total** (Counter) : compte le nombre total d'erreurs rencontrées par l'application. C'est la métrique la plus importante du point de vue de la sécurité : toute erreur inattendue est immédiatement visible.

**docchain_request_duration_seconds** (Histogram) : mesure la durée de chaque requête. Une augmentation anormale de la latence peut indiquer une surcharge, une attaque de type déni de service, ou un problème de connexion avec Azure Storage.

### 5.3 Dashboard Grafana

Un dashboard Grafana Cloud a été configuré sur `docchain.grafana.net` avec trois panels correspondant aux trois métriques ci-dessus. Le dashboard se rafraîchit automatiquement toutes les 10 secondes et affiche les données des 30 dernières minutes par défaut.

Grafana Cloud scrape les métriques de l'application toutes les minutes via un scrape job configuré sur l'endpoint `/metrics`.

### 5.4 Alertes configurées

Une règle d'alerte a été configurée dans Grafana :

- **Nom** : Taux erreurs DocChain
- **Condition** : `docchain_errors_total > 0` pendant plus de 2 minutes consécutives
- **Évaluation** : toutes les minutes
- **Notification** : webhook vers l'application
- **Justification** : dans une application de gestion de documents, toute erreur persistante est anormale et doit être investiguée immédiatement

---

## 6. Conformité RGPD

L'application DocChain peut être amenée à stocker des fichiers personnels (photos, documents d'identité, etc.). Les mesures suivantes ont été mises en place pour respecter le Règlement Général sur la Protection des Données :

**Minimisation des données** : seul le fichier et son nom sont stockés. Aucune donnée personnelle de l'utilisateur (email, nom, adresse IP) n'est conservée de manière permanente.

**Politique de rétention** : le script `cleanup.py` supprime automatiquement tous les fichiers de plus de 30 jours. Cette politique de rétention limite la durée de conservation des données au strict minimum.

**Chiffrement obligatoire** : toutes les données sont chiffrées au repos et en transit, conformément aux recommandations de la CNIL pour la protection des données personnelles.

**Droit à l'effacement** : techniquement, la suppression d'un fichier du Blob Storage est possible via le script d'administration ou l'interface Azure. Le hash de l'empreinte reste sur la blockchain (immuable par nature), mais sans le fichier d'origine, cette information est inutilisable.

**Hébergement en Europe** : toutes les ressources Azure sont déployées en région `West Europe` (Amsterdam), ce qui garantit que les données ne quittent pas le territoire européen et reste conforme au RGPD.

---

## 7. Sécurité de la blockchain

### 7.1 Choix du réseau Sepolia

Ethereum Sepolia est un réseau de test public qui reproduit exactement le comportement de la blockchain Ethereum principale, sans valeur financière réelle. Ce choix est justifié dans le contexte académique car il permet de démontrer l'intégration blockchain sans frais réels.

En production, le contrat serait déployé sur le réseau Ethereum principal ou sur un réseau Layer 2 moins coûteux comme Polygon ou Arbitrum.

### 7.2 Smart Contract DocumentRegistry

Le smart contract `DocumentRegistry.sol` a été développé en Solidity et déployé sur Sepolia :

- **Adresse du contrat** : `0xE1A55786068869B9318811f61931783600fc8FCf`
- **Réseau** : Ethereum Sepolia (Chain ID : 11155111)
- **Vérification** : visible sur Sepolia Etherscan

Le contrat expose deux fonctions principales :
- `registerDocument(bytes32 hash, string filename)` : enregistre l'empreinte d'un document
- `verifyDocument(bytes32 hash)` : vérifie si un document a été enregistré et retourne ses métadonnées

**Protection contre la double inscription** : le contrat vérifie qu'un hash n'a pas déjà été enregistré avant de l'accepter. Cela évite les doublons et garantit l'unicité de chaque document enregistré.

**Immuabilité** : une fois qu'un hash est enregistré dans la blockchain, il est impossible de le modifier ou de le supprimer. C'est cette propriété fondamentale de la blockchain qui garantit la preuve d'intégrité.

---

## 8. Scripts d'administration et automatisation

### 8.1 health_check.py

Ce script vérifie en temps réel que le Storage Azure est accessible et que le container `docchain` répond correctement. Il retourne un code de sortie 0 (succès) ou 1 (échec), ce qui permet de l'intégrer dans des systèmes de supervision automatisés.

En production, ce script serait exécuté toutes les 5 minutes via une Azure Function Timer Trigger.

### 8.2 cleanup.py

Ce script supprime automatiquement les fichiers de plus de 30 jours dans le Blob Storage. Il affiche un rapport détaillé de chaque fichier traité (conservé ou supprimé) avec son âge en jours.

Ce script est essentiel pour deux raisons : la conformité RGPD (politique de rétention) et la maîtrise des coûts Azure (éviter de payer pour du stockage inutile).

### 8.3 rotate_secrets.py

Ce script vérifie la validité des clés d'accès Azure Storage et simule leur rotation. En production, la rotation serait effectuée via Azure Key Vault, qui peut générer automatiquement de nouvelles clés et mettre à jour les références sans interruption de service.

La bonne pratique est de faire pivoter les clés d'accès tous les 90 jours maximum.

---

## 9. Tableau de synthèse des mesures de sécurité

| Catégorie | Mesure | Statut | Preuve |
|-----------|--------|--------|--------|
| Chiffrement transit | HTTPS uniquement sur App Service | ✅ Actif | azure-https.png |
| Chiffrement transit | TLS 1.2 minimum | ✅ Actif | azure-webapp-config.png |
| Chiffrement repos | SSE AES-256 sur Blob Storage | ✅ Actif | azure-chiffrement.png |
| Gestion des secrets | Aucun secret dans le code | ✅ Actif | .gitignore |
| Accès | Container Blob privé | ✅ Actif | azure-containers.png |
| Intégrité | Hash SHA-256 de chaque fichier | ✅ Actif | app-blockchain.png |
| Blockchain | Smart contract sur Sepolia | ✅ Déployé | blockchain-deployed.png |
| Monitoring | Dashboard Grafana Cloud | ✅ Actif | grafana-dashboard.png |
| Alertes | Alerte sur taux d'erreur | ✅ Configurée | grafana-alert-rules.png |
| IaC | Infrastructure versionnée Terraform | ✅ Actif | GitHub repo |
| RGPD | Rétention 30 jours automatique | ✅ Actif | scripts/cleanup.py |
| RGPD | Hébergement Europe (West Europe) | ✅ Actif | azure-resource-group.png |

---

## 10. Conclusion

La sécurisation de DocChain repose sur une approche en profondeur : chaque couche de l'application est sécurisée i