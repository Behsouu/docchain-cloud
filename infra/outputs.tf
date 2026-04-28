output "app_url" {
  description = "URL de l'application"
  value       = "https://${azurerm_linux_web_app.app.default_hostname}"
}

output "storage_connection_string" {
  description = "Chaîne de connexion Storage"
  value       = azurerm_storage_account.storage.primary_connection_string
  sensitive   = true
}

output "table_storage_name" {
  description = "Nom de la table Azure Storage pour les metadonnees"
  value       = azurerm_storage_table.documents.name
}