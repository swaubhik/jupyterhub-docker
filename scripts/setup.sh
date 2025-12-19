#!/bin/bash

# ============================================================================
# JupyterHub GPU Setup - Quick Start Script
# ============================================================================
# This script helps you quickly set up and verify your JupyterHub environment

set -e  # Exit on error

echo "============================================================================"
echo "JupyterHub Multi-User GPU Environment - Setup Script"
echo "============================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================

echo "Step 1: Checking prerequisites..."
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed!${NC}"
    echo "Please install Docker: https://docs.docker.com/engine/install/"
    exit 1
else
    echo -e "${GREEN}✓ Docker is installed${NC}"
    docker --version
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose plugin"
    exit 1
else
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
    docker compose version
fi

# Check NVIDIA Driver
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}✗ NVIDIA driver is not installed!${NC}"
    echo "Please install NVIDIA drivers"
    exit 1
else
    echo -e "${GREEN}✓ NVIDIA driver is installed${NC}"
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
fi

# Check NVIDIA Container Toolkit
if ! docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${YELLOW}⚠ NVIDIA Container Toolkit may not be properly configured${NC}"
    echo "Attempting to configure..."
    
    if command -v nvidia-ctk &> /dev/null; then
        sudo nvidia-ctk runtime configure --runtime=docker
        sudo systemctl restart docker
        echo -e "${GREEN}✓ Docker configured for NVIDIA runtime${NC}"
    else
        echo -e "${RED}✗ NVIDIA Container Toolkit is not installed!${NC}"
        echo "Install it with:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install -y nvidia-container-toolkit"
        echo "  sudo nvidia-ctk runtime configure --runtime=docker"
        echo "  sudo systemctl restart docker"
        exit 1
    fi
else
    echo -e "${GREEN}✓ NVIDIA Container Toolkit is working${NC}"
fi

echo ""

# ============================================================================
# Step 2: Configure Environment
# ============================================================================

echo "Step 2: Configuring environment..."
echo ""

if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    
    # Generate random key
    RANDOM_KEY=$(openssl rand -hex 32)
    
    # Update .env with generated key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/CHANGE_ME_GENERATE_RANDOM_HEX_KEY/$RANDOM_KEY/" .env
    else
        # Linux
        sed -i "s/CHANGE_ME_GENERATE_RANDOM_HEX_KEY/$RANDOM_KEY/" .env
    fi
    
    echo -e "${GREEN}✓ Created .env file with generated crypto key${NC}"
    echo -e "${YELLOW}⚠ You still need to add your CLOUDFLARE_TUNNEL_TOKEN to .env${NC}"
    echo ""
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create student data directory
if [ ! -d student-data ]; then
    mkdir -p student-data
    chmod 755 student-data
    echo -e "${GREEN}✓ Created student-data directory${NC}"
else
    echo -e "${GREEN}✓ student-data directory exists${NC}"
fi

echo ""

# ============================================================================
# Step 3: Build Images
# ============================================================================

echo "Step 3: Building Docker images..."
echo ""

docker compose build

echo -e "${GREEN}✓ Docker images built successfully${NC}"
echo ""

# ============================================================================
# Step 4: Final Checks
# ============================================================================

echo "============================================================================"
echo "Setup Complete! Ready to launch."
echo "============================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your Cloudflare Tunnel token:"
echo "   nano .env"
echo ""
echo "2. Configure admin users in users.txt:"
echo "   nano users.txt"
echo ""
echo "3. Start JupyterHub:"
echo "   docker compose up -d"
echo ""
echo "4. View logs:"
echo "   docker compose logs -f"
echo ""
echo "5. Access JupyterHub:"
echo "   - Local: http://localhost:8000"
echo "   - External: https://your-tunnel-url.com (after Cloudflare setup)"
echo ""
echo "============================================================================"
echo ""

# Ask if user wants to start now
read -p "Do you want to start JupyterHub now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if Cloudflare token is set
    if grep -q "YOUR_CLOUDFLARE_TUNNEL_TOKEN_HERE" .env; then
        echo -e "${YELLOW}⚠ Warning: Cloudflare Tunnel token not configured${NC}"
        echo "JupyterHub will start, but external access won't work."
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
    
    echo "Starting JupyterHub..."
    docker compose up -d
    echo ""
    echo -e "${GREEN}✓ JupyterHub is starting!${NC}"
    echo ""
    echo "View logs with: docker compose logs -f"
    echo "Access at: http://localhost:8000"
    echo ""
    
    # Wait a bit and show logs
    sleep 3
    echo "Recent logs:"
    docker compose logs --tail=20
fi
