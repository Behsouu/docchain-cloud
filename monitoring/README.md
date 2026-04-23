# Monitoring DocChain

## Architecture
- Flask expose les métriques sur /metrics (format Prometheus)
- Grafana Cloud scrape ces métriques toutes les minutes
- Dashboard disponible sur docchain.grafana.net

## Métriques exposées
| Métrique | Type | Description |
|----------|------|-------------|
| docchain_uploads_total | Counter | Nombre total de fichiers uploadés |
| docchain_errors_total | Counter | Nombre total d'erreurs |
| docchain_request_duration_seconds | Histogram | Durée des requêtes |

## Alertes configurées
- Taux d'erreur > 0 pendant 2 min → webhook notification