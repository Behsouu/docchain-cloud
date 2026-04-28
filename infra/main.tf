terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id            = var.subscription_id
  skip_provider_registration = true
}

# Resource Group — le conteneur de toutes tes ressources Azure
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags = {
    projet        = "docchain"
    etudiant      = "efrei"
    environnement = "dev"
  }
}

# Storage Account — pour stocker les fichiers (équivalent S3)
resource "azurerm_storage_account" "storage" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  blob_properties {
    delete_retention_policy {
      days = 7
    }
  }

  tags = {
    projet = "docchain"
  }
}

# Container Blob — le "dossier" dans le Storage Account
resource "azurerm_storage_container" "container" {
  name                  = "docchain"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

# Plan App Service — nécessaire pour héberger l'app Flask
resource "azurerm_service_plan" "plan" {
  name                = "docchain-plan"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "F1"
}

resource "azurerm_linux_web_app" "app" {
  name                = var.app_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id
  https_only          = true

  site_config {
    application_stack {
      python_version = "3.11"
    }
    always_on = false
  }

  app_settings = {
    "AZURE_STORAGE_CONNECTION_STRING" = azurerm_storage_account.storage.primary_connection_string
    "AZURE_CONTAINER_NAME"            = azurerm_storage_container.container.name
    "SCM_DO_BUILD_DURING_DEPLOYMENT"  = "true"
  }

  tags = {
    projet = "docchain"
  }
}

# Data source pour récupérer l'identité de l'utilisateur connecté
data "azurerm_client_config" "current" {}

# Azure Key Vault — stockage sécurisé des secrets
resource "azurerm_key_vault" "kv" {
  name                = "docchain-kv-sina"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get", "List", "Set", "Delete"
    ]
  }

  tags = {
    projet = "docchain"
  }
}

# Secret — clé de connexion Storage dans Key Vault
resource "azurerm_key_vault_secret" "storage_key" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.storage.primary_connection_string
  key_vault_id = azurerm_key_vault.kv.id
}

# Azure Table Storage — base de données managée pour les métadonnées documents
resource "azurerm_storage_table" "documents" {
  name                 = "documents"
  storage_account_name = azurerm_storage_account.storage.name
}

# VNet — Reseau virtuel prive pour isoler les ressources
resource "azurerm_virtual_network" "vnet" {
  name                = "docchain-vnet"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = ["10.0.0.0/16"]
  tags = { projet = "docchain" }
}

# Subnet public — pour l'App Service
resource "azurerm_subnet" "subnet_public" {
  name                 = "docchain-subnet-public"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
  delegation {
    name = "appservice-delegation"
    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

# Subnet prive — pour les services backend (Storage, Key Vault)
resource "azurerm_subnet" "subnet_private" {
  name                 = "docchain-subnet-private"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.2.0/24"]
}

# NSG — Regles de securite reseau
resource "azurerm_network_security_group" "nsg" {
  name                = "docchain-nsg"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  security_rule {
    name                       = "allow-https"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "deny-http"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = { projet = "docchain" }
}

# Association NSG - Subnet public
resource "azurerm_subnet_network_security_group_association" "nsg_assoc" {
  subnet_id                 = azurerm_subnet.subnet_public.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}