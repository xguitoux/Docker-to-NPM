# Projet : Orchestrateur Docker + NPM + OVH DNS

## Contexte

Ce projet vise à créer une interface self-service pour automatiser :
- La création de containers Docker
- La configuration automatique dans Nginx Proxy Manager (reverse proxy)
- La création des enregistrements DNS chez OVH
- La gestion automatique des subnets Docker

## Architecture cible

```
┌─────────────────────────────────────────────────────────┐
│                   Interface Web (Form)                   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   API Backend (FastAPI)                  │
│  - Validation des inputs                                 │
│  - Orchestration des appels                              │
└──────┬──────────────┬──────────────────┬────────────────┘
       │              │                  │
       ▼              ▼                  ▼
┌────────────┐  ┌───────────┐  ┌─────────────────┐
│  Docker    │  │    NPM    │  │   OVH API       │
│  Engine    │  │    API    │  │   (DNS)         │
└────────────┘  └───────────┘  └─────────────────┘
```

## Fonctionnalités attendues

### 1. Formulaire de création de service
- Nom du service (sera utilisé pour le subdomain)
- Image Docker (ou sélection parmi des templates prédéfinis)
- Port interne du container
- Variables d'environnement (optionnel)
- Volumes à monter (optionnel)
- Activer SSL (Let's Encrypt via NPM)

### 2. Orchestration automatique
À la soumission du formulaire :
1. **Réseau Docker** : Créer un subnet dédié ou réutiliser un réseau existant
2. **Container** : Déployer le container sur le réseau
3. **NPM** : Créer le proxy host (subdomain.domaine.tld → container:port)
4. **OVH DNS** : Créer l'enregistrement A/CNAME pointant vers le serveur

### 3. Gestion des subnets
- Pool de subnets disponibles (ex: 172.20.0.0/16 découpé en /24)
- Tracking des subnets utilisés (SQLite ou JSON)
- Attribution automatique du prochain subnet libre

## Stack technique

- **Backend** : Python + FastAPI
- **Frontend** : HTML/CSS/JS simple (ou Vue.js si besoin de plus de complexité)
- **Base de données** : SQLite (léger, pas besoin de plus)
- **APIs externes** :
  - Docker Engine API (socket Unix ou TCP)
  - Nginx Proxy Manager API (REST, port 81)
  - OVH API (REST, authentification par tokens)

## Configuration requise

### Variables d'environnement à définir

```bash

```

## Structure du projet (à créer)

```
orchestrator/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration / env vars
│   ├── models.py            # Pydantic models
│   ├── services/
│   │   ├── docker_service.py    # Interactions Docker
│   │   ├── npm_service.py       # Interactions NPM API
│   │   ├── ovh_service.py       # Interactions OVH API
│   │   └── subnet_manager.py    # Gestion des subnets
│   ├── database.py          # SQLite setup
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docker-compose.yml       # Pour déployer l'orchestrateur lui-même
├── .env.example
└── README.md
```

## APIs à intégrer

### NPM API (non documentée officiellement)

```bash
# Auth
POST /api/tokens
Body: {"identity": "email", "secret": "password"}
Response: {"token": "xxx"}

# Créer proxy host
POST /api/nginx/proxy-hosts
Headers: Authorization: Bearer xxx
Body: {
  "domain_names": ["sub.domain.tld"],
  "forward_host": "172.20.1.2",
  "forward_port": 8080,
  "forward_scheme": "http",
  "ssl_forced": true,
  "certificate_id": "new"  # ou ID existant
}

# Lister les proxy hosts
GET /api/nginx/proxy-hosts

# Supprimer
DELETE /api/nginx/proxy-hosts/{id}
```

### OVH API

Documentation : https://api.ovh.com/

```python
import ovh

client = ovh.Client(
    endpoint='ovh-eu',
    application_key='xxx',
    application_secret='xxx',
    consumer_key='xxx'
)

# Créer un enregistrement A
client.post(f'/domain/zone/{zone}/record',
    fieldType='A',
    subDomain='myapp',
    target='1.2.3.4',
    ttl=3600
)

# Refresh la zone
client.post(f'/domain/zone/{zone}/refresh')
```

### Docker SDK Python

```python
import docker

client = docker.from_env()

# Créer un réseau
network = client.networks.create(
    "myapp-network",
    driver="bridge",
    ipam=docker.types.IPAMConfig(
        pool_configs=[docker.types.IPAMPool(subnet="172.20.1.0/24")]
    )
)

# Créer un container
container = client.containers.run(
    "nginx:latest",
    name="myapp",
    detach=True,
    network="myapp-network",
    environment={"FOO": "bar"},
    ports={'80/tcp': None}  # ou mapping spécifique
)
```

## Commandes utiles

```bash
# Lancer le backend en dev
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Tester l'API
curl http://localhost:8000/health

# Voir les logs NPM
docker logs nginx-proxy-manager

# Tester la connexion OVH
python -c "import ovh; c = ovh.Client(); print(c.get('/me'))"
```

## Notes importantes

- L'API NPM n'est pas officiellement documentée, elle peut changer entre versions
- Pour les certificats SSL, NPM peut générer des Let's Encrypt automatiquement si le DNS est déjà configuré
- L'ordre des opérations est important : DNS d'abord (propagation), puis NPM avec SSL
- Prévoir un délai ou une vérification de propagation DNS avant de demander le certificat

## TODO / Roadmap

- [ ] Setup du projet de base
- [ ] Service Docker (create network, container)
- [ ] Service OVH (create DNS record)
- [ ] Service NPM (create proxy host)
- [ ] Subnet manager
- [ ] API endpoints FastAPI
- [ ] Frontend formulaire
- [ ] Gestion des erreurs / rollback
- [ ] Templates de services prédéfinis (Nextcloud, Gitea, etc.)
- [ ] Interface de listing / suppression des services
- [ ] Authentification sur l'interface

## Questions ouvertes à clarifier

- Quel est le domaine principal utilisé ?
- NPM tourne-t-il déjà ? Sur quelle machine ?
- Faut-il gérer plusieurs serveurs ou un seul ?
- Y a-t-il des templates de containers à prédéfinir ?
- Niveau d'authentification souhaité sur l'interface ?
