#!/bin/bash

# Script pour servir le frontend en mode développement

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Docker Orchestrator - Frontend ===${NC}\n"

# Vérifier si python3 est disponible
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 n'est pas installé!${NC}"
    exit 1
fi

echo -e "${GREEN}Démarrage du serveur frontend...${NC}"
echo -e "${BLUE}Frontend disponible sur: http://localhost:8080${NC}\n"
echo -e "${BLUE}Note: Le backend doit être lancé séparément avec ./run-dev.sh${NC}\n"

cd frontend && python3 -m http.server 8080
