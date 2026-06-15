#!/bin/bash

# Configuration
VENV_DIR=".venv"
PYTHON_BIN="python3"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Iniciando sistema Coletor-SUAP...${NC}"

# Check if Python 3 is installed
if ! command -v $PYTHON_BIN &> /dev/null; then
    echo "Erro: $PYTHON_BIN não está instalado. Por favor, instale o Python 3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}Criando ambiente virtual em $VENV_DIR...${NC}"
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo -e "${BLUE}Ativando ambiente virtual...${NC}"
source "$VENV_DIR/bin/activate"

# Install/Update dependencies
echo -e "${BLUE}Instalando/Atualizando dependências...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo -e "${BLUE}Instalando navegadores do Playwright...${NC}"
playwright install

# Navigate to project root
cd "$(dirname "$0")/.."

# Create directories for data and logs
mkdir -p data/raw
mkdir -p data/processed
mkdir -p logs

# Run the application
echo -e "${GREEN}O sistema está pronto! Iniciando o servidor Flask...${NC}"
echo -e "${BLUE}Acesse a aplicação em http://localhost:5000${NC}"
export PYTHONPATH=$PYTHONPATH:.
python main.py
