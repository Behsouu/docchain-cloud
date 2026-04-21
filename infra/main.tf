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
  subscription_id             = var.subscription_id
  skip_provider_registration  = true
}

# Resource Group — le conteneur de toutes tes ressources Azure
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags = {
    projet      = "docchain"
    etudiant    = "efrei"
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

# Web App — héberge l'application Flask
resource "azurerm_linux_web_app" "app" {
  name                = var.app_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

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