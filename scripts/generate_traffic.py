import requests, time, os

BASE_URL = "http://127.0.0.1:5000"

print("Génération de trafic pour Grafana...")
for i in range(20):
    # Requête homepage
    requests.get(f"{BASE_URL}/")
    print(f"  Requête {i+1}/20 — GET /")
    
    # Requête metrics
    requests.get(f"{BASE_URL}/metrics")
    print(f"  Requête {i+1}/20 — GET /metrics")
    
    time.sleep(2)

print("Terminé !")