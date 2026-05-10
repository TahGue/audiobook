#!/bin/bash

# Audiobook Maker Backend Startup Script
# Usage: ./start.sh [dev|prod|worker]

set -e

MODE=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Audiobook Maker Backend ===${NC}"
echo "Mode: $MODE"
echo ""

# Check Python
echo -e "${BLUE}Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found${NC}"
    exit 1
fi

python3 --version

# Setup virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Create directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p audio cache models

# Run database migrations
echo -e "${BLUE}Running database migrations...${NC}"
alembic upgrade head

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo -e "${BLUE}Loading environment from .env${NC}"
    set -a
    source .env
    set +a
fi

case $MODE in
    dev)
        echo -e "${GREEN}Starting development server...${NC}"
        echo "API will be available at: http://localhost:8001"
        echo "API docs: http://localhost:8001/docs"
        echo ""
        uvicorn main:app --reload --host 0.0.0.0 --port 8001
        ;;
    
    prod)
        echo -e "${GREEN}Starting production server...${NC}"
        echo "API will be available at: http://localhost:8001"
        echo ""
        # Use more workers for production
        uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2
        ;;
    
    worker)
        echo -e "${GREEN}Starting ARQ worker...${NC}"
        echo "Worker will process TTS jobs from Redis queue"
        echo ""
        arq worker.WorkerSettings
        ;;
    
    *)
        echo -e "${YELLOW}Usage: $0 [dev|prod|worker]${NC}"
        echo ""
        echo "Modes:"
        echo "  dev     - Development server with auto-reload (default)"
        echo "  prod    - Production server with multiple workers"
        echo "  worker  - ARQ background job worker"
        exit 1
        ;;
esac
