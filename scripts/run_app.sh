#!/bin/bash

# --- CONFIGURATION ---
PROJECT_NAME="Nebula AI Onboarding"
VENV_PATH="venv"
BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8000"
DB_PATH="./chroma_db"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Initializing ${PROJECT_NAME}...${NC}"

# 1. Activate Virtual Environment
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
else
    echo -e "${RED}Virtual environment not found.${NC}"
    echo "Please run ./init_project.sh first."
    exit 1
fi

# 2. PRE-FLIGHT CHECK: Database Health
echo -e "${BLUE}Checking Knowledge Base status...${NC}"

# We run a small python snippet to count docs in the DB
DOC_COUNT=$(python3 -c '
try:
    from langchain_chroma import Chroma
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    if not os.path.exists("./chroma_db"):
        print("0")
        exit()

    embedding = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    db = Chroma(persist_directory="./chroma_db", embedding_function=embedding)
    print(db._collection.count())
except Exception:
    print("0")
')

if [ "$DOC_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}Warning: The Vector Database is empty! (Doc Count: 0)${NC}"
    echo "The AI will not be able to answer policy questions."
    
    read -p "DO YOU WANT TO RUN INGESTION NOW? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Running Ingestion Script...${NC}"
        python3 rag_engine/ingestion/ingest.py
        
        # Verify again
        if [ $? -ne 0 ]; then
             echo -e "${RED}Ingestion failed. Fix errors and try again.${NC}"
             exit 1
        fi
    else
        echo -e "${RED}🛑 Aborting startup. System needs data to run.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Database Healthy (${DOC_COUNT} documents loaded).${NC}"
fi

# 3. Define Cleanup Function
cleanup() {
    echo -e "\n${RED}🛑 Shutting down...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID
    fi
    deactivate
    exit
}
trap cleanup SIGINT

# 4. Start Backend
echo -e "${GREEN}Launching FastAPI Backend...${NC}"
uvicorn backend.app.main:app --host $BACKEND_HOST --port $BACKEND_PORT --reload &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for API..."
sleep 3

# 5. Start Frontend
echo -e "${GREEN}Launching Streamlit Frontend...${NC}"
streamlit run frontend/app.py

cleanup