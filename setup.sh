#!/bin/bash
# IndoGap Installation Script
# Installs all dependencies and Ollama models for local AI

set -e  # Exit on error

echo "=========================================="
echo "IndoGap AI Engine - Installation Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check Python version
echo ""
echo "Checking Python version..."
python3 --version || { print_error "Python 3 not found"; exit 1; }
print_status "Python 3 found"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -q -r requirements.txt 2>/dev/null || \
    uv pip install -r requirements.txt 2>/dev/null || \
    python3 -m pip install -r requirements.txt
print_status "Python dependencies installed"

# Check/Install Ollama
echo ""
echo "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    print_status "Ollama is already installed"
    ollama --version
else
    print_warning "Ollama not found. Installing..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux installation
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install ollama
    else
        print_warning "Please install Ollama manually from https://ollama.ai"
    fi
fi

# Pull AI models
echo ""
echo "=========================================="
echo "Installing Local AI Models"
echo "=========================================="

# Model sizes and requirements
# - llama3.2:3b ~2GB RAM (fast tasks, classification)
# - llama3.1:8b ~5GB RAM (reasoning, analysis) 
# - deepseek-coder:6.7b ~4GB RAM (code generation)

print_status "Pulling Llama 3.2 3B (fast classification)..."
ollama pull llama3.2:3b

print_status "Pulling Llama 3.1 8B (reasoning & analysis)..."
ollama pull llama3.1:8b

print_status "Pulling DeepSeek Coder 6.7B (code generation)..."
ollama pull deepseek-coder:6.7b

# Verify models
echo ""
echo "Verifying installed models..."
ollama list

# Create .env file
echo ""
echo "Creating configuration file..."
cat > .env << EOF
# IndoGap Configuration
# All settings for local AI-powered opportunity discovery

# API Settings
INDOGAP_OPENAI_API_KEY=  # Not needed - using local Ollama!

# Ollama Settings (Local AI)
INDOGAP_OLLAMA_HOST=http://localhost:11434
INDOGAP_OLLAMA_TIMEOUT=120

# Scraping Settings
INDOGAP_YC_SCRAPE_DELAY=1.0
INDOGAP_PRODUCT_HUNT_SCRAPE_DELAY=2.0
INDOGAP_REQUEST_TIMEOUT=30

# Scoring Weights
INDOGAP_SCORING_WEIGHTS={"cultural_fit":0.15,"logistics":0.15,"payment_readiness":0.15,"timing":0.15,"monopoly_potential":0.10,"regulatory_risk":0.15,"execution_feasibility":0.15}

# Similarity Thresholds
INDOGAP_SIMILARITY_THRESHOLD_HIGH=0.7
INDOGAP_SIMILARITY_THRESHOLD_LOW=0.3
INDOGAP_MIN_SCORE_THRESHOLD=0.5

# Logging
INDOGAP_LOG_LEVEL=INFO
EOF

print_status "Configuration file created: .env"

# Start Ollama in background
echo ""
echo "=========================================="
echo "Starting Ollama Service"
echo "=========================================="

# Export environment variables
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_KEEP_ALIVE=0  # Unload models immediately after use (memory optimization)

# Start Ollama if not running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_warning "Starting Ollama service in background..."
    ollama serve &
    sleep 3
fi

# Verify Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_status "Ollama is running"
else
    print_warning "Ollama may not be running. Start manually with: ollama serve"
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "To start the IndoGap dashboard:"
echo "  python api_server.py"
echo ""
echo "Then open your browser to:"
echo "  http://localhost:8000"
echo ""
echo "For CLI usage:"
echo "  python main.py --demo"
echo ""
echo "Note: Make sure Ollama is running before using the AI features!"
echo ""
