#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Data Quality Platform - Local Setup${NC}\n"

# Check Python
echo -e "${BLUE}✓ Checking Python installation...${NC}"
python --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}✓ Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo -e "${BLUE}✓ Installing dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1

# Create necessary directories
mkdir -p uploads logs

echo -e "\n${GREEN}✓ Setup complete!${NC}\n"

echo -e "${BLUE}📝 To start the application:${NC}"
echo -e "\n${GREEN}Terminal 1 - Start Backend:${NC}"
echo "   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo -e "${GREEN}Terminal 2 - Start Frontend:${NC}"
echo "   cd frontend-react && npm install && npm run dev"
echo ""
echo -e "${BLUE}Then open:${NC}"
echo "   API:      http://localhost:8000/docs"
echo "   Frontend: http://localhost:3000"
echo ""
