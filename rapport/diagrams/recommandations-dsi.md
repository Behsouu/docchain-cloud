# Recommandations à la DSI — WebMarket+

## Contexte

WebMarket+ fait face à des contraintes classiques d'un SI hébergé sur serveur dédié : 
incapacité à absorber les pics de charge (soldes, fêtes), manque de visibilité sur les 
coûts, risques sécurité, et dépendance opérationnelle forte. La migration vers Azure 
constitue un levier stratégique majeur.

---

## 1. Modèle de Responsabilité Partagée

Dans une architecture cloud, les responsabilités sont partagées entre WebMarket+ et 
Microsoft Azure selon le modèle PaaS choisi :

**WebMarket+ reste responsable de :**
- Le code applicatif et sa qualité
- La gestion des identités et des droits IAM
- La configuration des secrets et des clés d'accès
- Les données clients et leur conformité RGPD
- Le smart contract Solidity et sa logique métier

**Microsoft Azure prend en charge :**
- L'infrastructure physique (datacenter, réseau, alimentation)
- L'hyperviseur et la virtualisation
- Le chiffrement au repos (AES-256) et en transit (TLS 1.2)
- Les patches de sécurité de l'OS
- Le SLA de disponibilité (99.95% sur App Service)

Ce modèle libère l'équipe interne des tâches d'exploitation bas niveau 
et réduit la dépendance à l'équipe IT interne.

---

## 2. Haute Disponibilité et Résilience

**Situation actuelle :** serveur dédié = point unique de défaillance (SPOF).
Si le serveur tombe, l'application est inaccessible.

**Solution Azure :** Azure App Service garantit un SLA de 99.95%, soit moins de 
4,5 heures d'indisponibilité par an. La réplication LRS du Blob Storage assure 
3 copies des données dans la même région.

**Actions recommandées à court terme :**
- Activer les Health Checks sur l'App Service
- Configurer une stratégie de backup automatique du Storage (rétention 30 jours)
- Mettre en place Azure Front Door pour la résilience multi-région à moyen terme

---

## 3. Élasticité vs Scalabilité

Ces deux concepts sont souvent confondus mais distincts :

**Scalabilité** = capacité à monter en charge de manière planifiée.
Exemple : passer de 2 à 10 instances avant les soldes de janvier.

**Élasticité** = capacité à s'adapter automatiquement à la charge en temps réel.
Exemple : Azure Auto-scale ajoute une instance en 5 minutes si le CPU dépasse 70%, 
puis la supprime automatiquement quand la charge baisse.

**Recommandation :** configurer l'Auto-scale sur l'App Service avec :
- Minimum : 1 instance (coût minimal)
- Maximum : 5 instances (protection contre les coûts excessifs)
- Déclencheur : CPU > 70% pendant 5 minutes

**Impact estimé :** absorption des pics de charge des soldes sans intervention manuelle, 
réduction des coûts de 40-60% par rapport à une infrastructure dimensionnée pour le pic.

---

## 4. Cycle de Vie des Données et FinOps

**Problème actuel :** tous les fichiers sont stockés au même coût quelle que soit 
leur fréquence d'accès.

**Solution Azure Blob Lifecycle Management :**

| Âge du fichier | Tier de stockage | Coût/Go/mois | Économie |
|---|---|---|---|
| 0-30 jours | Hot | 0.018€ | Référence |
| 30-90 jours | Cool | 0.010€ | -44% |
| 90-365 jours | Cold | 0.004€ | -78% |
| > 365 jours | Archive | 0.001€ | -94% |

**Recommandation :** activer une politique de cycle de vie qui archive 
automatiquement les fichiers selon leur âge. Économie estimée pour WebMarket+ : 
30-50% sur les coûts de stockage à 12 mois.

---

## 5. Actions Prioritaires

**Court terme (0-3 mois) :**
1. Déployer l'architecture Azure via Terraform (fait)
2. Activer Azure Key Vault pour tous les secrets sensibles
3. Configurer le monitoring Grafana avec alertes
4. Mettre en place la politique de rétention RGPD (30 jours)

**Moyen terme (3-12 mois) :**
1. Configurer l'Auto-scaling pour les pics de charge
2. Activer le Lifecycle Management du Blob Storage
3. Mettre en place Azure CDN pour les assets statiques
4. Déployer le smart contract sur le mainnet Ethereum

**Risques à anticiper :**
- Dépassement du budget Azure for Students (surveiller via Azure Cost Management)
- Latence des transactions blockchain en production (prévoir mode asynchrone)
- Conformité RGPD : vérifier que les données ne quittent pas la région EU