#!/bin/bash

# Change to the project root directory (one level up from scripts/)
cd "$(dirname "$0")/.." || exit 1

# --- CONFIGURATION ---
PROJECT_NAME="Nebula-onboarding"
VENV_DIR="venv"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Initializing ${PROJECT_NAME}...${NC}"

# 1. Create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "Virtual environment already exists."
fi

# 2. Upgrade PIP
echo "Upgrading pip..."
./$VENV_DIR/bin/python -m pip install --upgrade pip

# 3. Install Requirements
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    # This forces installation into the venv, even if not active
    ./$VENV_DIR/bin/pip install -r requirements.txt
    
    # Explicitly install pytest (just in case it was missed)
    ./$VENV_DIR/bin/pip install pytest requests
    
    echo -e "${GREEN}Dependencies installed successfully.${NC}"
else
    echo -e "${RED}requirements.txt not found!${NC}"
fi

# 4. Setup .env
if [ ! -f ".env" ]; then
    echo "OPENAI_API_KEY=your-key-here" > .env
    echo "GOOGLE_API_KEY=your-key-here" >> .env
    echo "Created .env file."
fi

echo "==========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "IMPORTANT: To run commands manually, you must run:"
echo -e "${BLUE}source venv/bin/activate${NC}"
echo "==========================================="