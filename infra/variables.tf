variable "subscription_id" {
  description = "ID de la subscription Azure"
  type        = string
}

variable "resource_group_name" {
  description = "Nom du resource group"
  type        = string
  default     = "docchain-rg"
}

variable "location" {
  description = "Région Azure"
  type        = string
  default     = "West Europe"
}

variable "storage_account_name" {
  description = "Nom du storage account (minuscules, 3-24 caractères)"
  type        = string
}

variable "app_name" {
  description = "Nom de l'application web (doit être unique globalement)"
  type        = string
}

variable "alchemy_url" {
  description = "URL Alchemy pour Ethereum Sepolia"
  type        = string
  default     = ""
}

variable "contract_address" {
  description = "Adresse du smart contract Ethereum"
  type        = string
  default     = "0xE1A55786068869B9318811f61931783600fc8FCf"
}

variable "wallet_private_key" {
  description = "Cle privee du wallet Ethereum (sensible)"
  type        = string
  sensitive   = true
  default     = ""
}