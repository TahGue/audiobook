#!/bin/bash

# Audiobook Maker - Unified Startup Script
# Usage: ./start.sh [web|desktop|backend|worker|all]

set -e

MODE=${1:-web}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Audiobook Maker ===${NC}"
echo "Starting: $MODE"
echo ""

show_help() {
    echo -e "${YELLOW}Usage: $0 [MODE]${NC}"
    echo ""
    echo "Modes:"
    echo "  web       - Start web frontend + backend (default)"
    echo "  desktop   - Start Tauri desktop app"
    echo "  backend   - Start backend API only"
    echo "  worker    - Start ARQ job worker"
    echo "  all       - Start everything (backend + frontend + worker)"
    echo ""
    echo "Examples:"
    echo "  $0 web       # Development mode"
    echo "  $0 desktop   # Desktop app"
    echo "  $0 all       # Full stack"
}

start_backend() {
    echo -e "${BLUE}Starting Backend...${NC}"
    cd backend
    ./start.sh dev &
    BACKEND_PID=$!
    cd ..
    echo $BACKEND_PID
}

start_worker() {
    echo -e "${BLUE}Starting ARQ Worker...${NC}"
    cd backend
    ./start.sh worker &
    WORKER_PID=$!
    cd ..
    echo $WORKER_PID
}

start_frontend() {
    echo -e "${BLUE}Starting Frontend...${NC}"
    cd frontend
    npm install
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo $FRONTEND_PID
}

case $MODE in
    web)
        echo -e "${GREEN}Starting Web Development Mode${NC}"
        echo ""
        
        # Start backend in background
        cd backend
        ./start.sh dev &
        BACKEND_PID=$!
        cd ..
        
        # Wait for backend to start
        echo "Waiting for backend..."
        sleep 3
        
        # Start frontend
        cd frontend
        echo -e "${GREEN}Starting frontend...${NC}"
        npm install
        npm run dev
        
        # Cleanup on exit
        trap "kill $BACKEND_PID 2>/dev/null; exit" INT
        ;;
    
    desktop)
        echo -e "${GREEN}Starting Desktop App${NC}"
        echo ""
        
        # Check if sidecar binary exists
        if [ ! -f "frontend/src-tauri/binaries/audiobook-backend" ]; then
            echo -e "${YELLOW}Python sidecar not found. Building...${NC}"
            cd backend
            python3 build_sidecar.py
            cd ..
        fi
        
        # Start Tauri
        cd frontend
        npm install
        npm run tauri:dev
        ;;
    
    backend)
        cd backend
        ./start.sh dev
        ;;
    
    worker)
        cd backend
        ./start.sh worker
        ;;
    
    all)
        echo -e "${GREEN}Starting Full Stack (Backend + Frontend + Worker)${NC}"
        echo ""
        
        # Start Redis if available
        if command -v redis-server &> /dev/null; then
            echo -e "${BLUE}Starting Redis...${NC}"
            redis-server --daemonize yes
        fi
        
        # Start backend
        cd backend
        ./start.sh dev &
        BACKEND_PID=$!
        cd ..
        
        # Start worker
        cd backend
        ./start.sh worker &
        WORKER_PID=$!
        cd ..
        
        # Wait for services
        sleep 3
        
        # Start frontend
        cd frontend
        npm install
        npm run dev &
        FRONTEND_PID=$!
        cd ..
        
        echo ""
        echo -e "${GREEN}All services started!${NC}"
        echo "  Backend:  http://localhost:8001"
        echo "  Frontend: http://localhost:5173"
        echo ""
        echo "Press Ctrl+C to stop all services"
        
        # Cleanup
        trap "kill $BACKEND_PID $WORKER_PID $FRONTEND_PID 2>/dev/null; exit" INT
        wait
        ;;
    
    help|--help|-h)
        show_help
        exit 0
        ;;
    
    *)
        echo -e "${RED}Unknown mode: $MODE${NC}"
        show_help
        exit 1
        ;;
esac
