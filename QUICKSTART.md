# Guide de démarrage rapide

## Installation et configuration

### 1. Environnement Python

Le projet utilise un environnement virtuel Python pour éviter les conflits de dépendances.

```bash
# L'environnement virtuel est déjà créé dans le dossier venv/
# Les dépendances sont déjà installées
```

### 2. Configuration des variables d'environnement

Le fichier `.env` contient déjà vos credentials. Vérifiez qu'il est correct :

```bash
cat .env
```

Si vous devez le modifier :

```bash
nano .env
```

## Démarrage en mode développement

### Option 1 : Scripts automatiques (recommandé)

**Terminal 1 - Backend :**
```bash
./run-dev.sh
```

**Terminal 2 - Frontend :**
```bash
./run-frontend.sh
```

### Option 2 : Commandes manuelles

**Backend :**
```bash
source venv/bin/activate
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend :**
```bash
cd frontend
python3 -m http.server 8080
```

## Accès à l'application

- **Interface web** : http://localhost:8080
- **API Backend** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **Health check** : http://localhost:8000/health

## Démarrage avec Docker Compose (Production)

```bash
# Construire et démarrer
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

L'application sera disponible sur http://localhost:8080

## Test de santé du système

Vérifiez que tous les services sont accessibles :

```bash
curl http://localhost:8000/health
```

Vous devriez voir :
```json
{
  "status": "healthy",
  "docker": true,
  "npm": true,
  "ovh": true
}
```

## Premiers pas

1. Ouvrez http://localhost:8080 dans votre navigateur
2. Vérifiez le statut système (Docker, NPM, OVH doivent être "OK")
3. Remplissez le formulaire pour créer votre premier service
4. Suivez la création dans la liste des services

## Dépannage

### "pip install ne fonctionne pas"

Le système utilise un environnement virtuel. Activez-le d'abord :

```bash
source venv/bin/activate
pip install -r backend/requirements.txt
```

### "Docker connection failed"

Vérifiez que Docker est en cours d'exécution :

```bash
docker ps
```

Vérifiez la variable `DOCKER_HOST` dans `.env`

### "NPM authentication failed"

Vérifiez que Nginx Proxy Manager est accessible :

```bash
curl http://192.168.1.11:81/api/schema
```

Vérifiez les credentials dans `.env`

### "OVH API errors"

Testez vos credentials OVH :

```bash
source venv/bin/activate
python3 -c "import ovh; from backend.config import settings; c = ovh.Client(endpoint=settings.ovh_endpoint, application_key=settings.ovh_application_key, application_secret=settings.ovh_application_secret, consumer_key=settings.ovh_consumer_key); print(c.get('/me'))"
```

## Commandes utiles

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Désactiver l'environnement virtuel
deactivate

# Voir les services déployés
curl http://localhost:8000/api/services | python3 -m json.tool

# Supprimer un service
curl -X DELETE http://localhost:8000/api/services/nom-du-service
```
