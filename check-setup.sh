#!/bin/bash

# Script de vérification de l'installation

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Docker Orchestrator - Vérification Setup     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}\n"

ERRORS=0
WARNINGS=0

# Fonction pour afficher un check
check_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

check_error() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# 1. Vérifier Python
echo -e "\n${BLUE}[1/8] Vérification Python${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    check_ok "Python installé: $PYTHON_VERSION"
else
    check_error "Python3 n'est pas installé"
fi

# 2. Vérifier environnement virtuel
echo -e "\n${BLUE}[2/8] Vérification environnement virtuel${NC}"
if [ -d "venv" ]; then
    check_ok "Environnement virtuel créé"

    # Vérifier si les packages sont installés
    if [ -f "venv/bin/python" ]; then
        if venv/bin/python -c "import fastapi" 2>/dev/null; then
            check_ok "Dépendances Python installées"
        else
            check_warning "Dépendances Python non installées (lancez: source venv/bin/activate && pip install -r backend/requirements.txt)"
        fi
    fi
else
    check_warning "Environnement virtuel non créé (lancez: python3 -m venv venv)"
fi

# 3. Vérifier fichier .env
echo -e "\n${BLUE}[3/8] Vérification configuration${NC}"
if [ -f ".env" ]; then
    check_ok "Fichier .env présent"

    # Vérifier les variables importantes
    if grep -q "OVH_APPLICATION_KEY=" .env && ! grep -q "OVH_APPLICATION_KEY=your_" .env; then
        check_ok "OVH credentials configurés"
    else
        check_warning "OVH credentials à configurer dans .env"
    fi

    if grep -q "NPM_PASSWORD=" .env && ! grep -q "NPM_PASSWORD=your_" .env; then
        check_ok "NPM credentials configurés"
    else
        check_warning "NPM credentials à configurer dans .env"
    fi
else
    check_error "Fichier .env manquant (copiez .env.example vers .env)"
fi

# 4. Vérifier Docker
echo -e "\n${BLUE}[4/8] Vérification Docker${NC}"
if command -v docker &> /dev/null; then
    check_ok "Docker installé"

    if docker ps &> /dev/null; then
        check_ok "Docker accessible"
    else
        check_error "Docker n'est pas accessible (permissions ou service arrêté)"
    fi
else
    check_error "Docker n'est pas installé"
fi

# 5. Vérifier Docker Compose
echo -e "\n${BLUE}[5/8] Vérification Docker Compose${NC}"
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    check_ok "Docker Compose installé"
else
    check_warning "Docker Compose n'est pas installé (optionnel pour dev)"
fi

# 6. Vérifier les fichiers du projet
echo -e "\n${BLUE}[6/8] Vérification structure du projet${NC}"
FILES=("backend/main.py" "backend/config.py" "backend/database.py" "frontend/index.html" "docker-compose.yml")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        check_ok "Fichier $file présent"
    else
        check_error "Fichier $file manquant"
    fi
done

# 7. Vérifier connectivité NPM (si configuré)
echo -e "\n${BLUE}[7/8] Test connectivité Nginx Proxy Manager${NC}"
if [ -f ".env" ]; then
    NPM_URL=$(grep "NPM_URL=" .env | cut -d'=' -f2)
    if [ ! -z "$NPM_URL" ] && [ "$NPM_URL" != "http://192.168.1.11:81/" ]; then
        if curl -s -o /dev/null -w "%{http_code}" "${NPM_URL}api/schema" | grep -q "200"; then
            check_ok "NPM accessible à $NPM_URL"
        else
            check_warning "NPM non accessible à $NPM_URL (vérifiez que NPM est démarré)"
        fi
    else
        check_warning "URL NPM à configurer dans .env"
    fi
fi

# 8. Vérifier les scripts de démarrage
echo -e "\n${BLUE}[8/8] Vérification scripts de démarrage${NC}"
if [ -x "run-dev.sh" ]; then
    check_ok "Script run-dev.sh exécutable"
else
    check_warning "Script run-dev.sh non exécutable (lancez: chmod +x run-dev.sh)"
fi

if [ -x "run-frontend.sh" ]; then
    check_ok "Script run-frontend.sh exécutable"
else
    check_warning "Script run-frontend.sh non exécutable (lancez: chmod +x run-frontend.sh)"
fi

# Résumé
echo -e "\n${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Résumé de la vérification         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}\n"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ Tout est prêt ! Vous pouvez démarrer l'application.${NC}\n"
    echo -e "${BLUE}Commandes pour démarrer :${NC}"
    echo -e "  Terminal 1: ${GREEN}./run-dev.sh${NC}"
    echo -e "  Terminal 2: ${GREEN}./run-frontend.sh${NC}\n"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS avertissement(s) détecté(s)${NC}"
    echo -e "L'application peut fonctionner mais certaines fonctionnalités peuvent être limitées.\n"
    exit 0
else
    echo -e "${RED}✗ $ERRORS erreur(s) et $WARNINGS avertissement(s) détecté(s)${NC}"
    echo -e "Corrigez les erreurs avant de démarrer l'application.\n"
    exit 1
fi
