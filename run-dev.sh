#!/bin/bash

# Script pour lancer l'orchestrateur en mode développement

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Docker Orchestrator - Mode Développement ===${NC}\n"

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo -e "${RED}Environnement virtuel non trouvé. Création...${NC}"
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo -e "${GREEN}Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

# Vérifier si les dépendances sont installées
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${BLUE}Installation des dépendances...${NC}"
    pip install -r backend/requirements.txt
fi

# Vérifier si le fichier .env existe
if [ ! -f ".env" ]; then
    echo -e "${RED}Fichier .env non trouvé!${NC}"
    echo -e "${BLUE}Création depuis .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}IMPORTANT: Éditez le fichier .env avec vos credentials avant de continuer!${NC}"
    exit 1
fi

# Lancer le serveur
echo -e "${GREEN}Démarrage du serveur FastAPI...${NC}"
echo -e "${BLUE}API disponible sur: http://localhost:8000${NC}"
echo -e "${BLUE}Documentation: http://localhost:8000/docs${NC}\n"

cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
