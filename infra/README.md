# Infrastructure DocChain — Terraform (C22)

## Ressources provisionnées (7 au total)

| Ressource | Nom | Justification |
|---|---|---|
| Resource Group | docchain-rg | Conteneur logique de toutes les ressources |
| Storage Account | docchainsinara | Stockage fichiers AES-256, LRS West Europe |
| Blob Container | docchain | Accès privé, rétention 7 jours |
| App Service Plan | docchain-plan | Plan F1 gratuit, Linux |
| Linux Web App | docchain-sina-efrei | Hébergement Flask, HTTPS forcé |
| Key Vault | docchain-kv-sina | Stockage sécurisé des secrets |
| KV Secret | storage-connection-string | Chaîne connexion Storage |

## Pourquoi Terraform ? (C22.2)

- Déclaratif : on décrit l'état voulu, Terraform calcule les actions
- Reproductible : `terraform apply` deux fois = même résultat
- Versionné : chaque modification est tracée dans Git
- Preuve : `terraform apply` → `No changes` = infrastructure stable

## Commandes

terraform init    # Initialise le provider azurerm
terraform plan    # Visualise les changements
terraform apply   # Applique l'infrastructure
terraform output  # Affiche l'URL de l'app et les outputs