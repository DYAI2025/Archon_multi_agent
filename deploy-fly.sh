#!/bin/bash

# ========================================================================
# 🚀 Fly.io Deployment - Archon MCP Server
# ========================================================================
# Nutzt einen deiner 3 kostenlosen Fly.io Slots
# ========================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              🚀 FLY.IO DEPLOYMENT - ARCHON MCP 🚀           ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo -e "${YELLOW}Installing Fly CLI...${NC}"
    curl -L https://fly.io/install.sh | sh
    export FLYCTL_INSTALL="/Users/benjaminpoersch/.fly"
    export PATH="$FLYCTL_INSTALL/bin:$PATH"
fi

# Login check
echo -e "${YELLOW}Checking Fly.io login...${NC}"
if ! fly auth whoami &> /dev/null; then
    echo -e "${CYAN}Please login to Fly.io:${NC}"
    fly auth login
fi

# Show current apps
echo -e "${CYAN}Your current Fly.io apps:${NC}"
fly apps list

echo
echo -e "${YELLOW}You have 3 free slots on Fly.io${NC}"
echo -e "${CYAN}Do you want to:${NC}"
echo "1) Deploy Archon MCP as new app"
echo "2) Replace an existing app"
echo "3) Cancel"
read -p "Choose (1-3): " choice

case $choice in
    1)
        echo -e "${GREEN}Creating new Fly.io app...${NC}"
        fly launch --name archon-mcp --region fra --no-deploy
        
        echo -e "${GREEN}Setting secrets...${NC}"
        # Add any API keys if needed
        # fly secrets set OPENAI_API_KEY=xxx
        
        echo -e "${GREEN}Deploying...${NC}"
        fly deploy
        
        echo -e "${GREEN}✅ Deployed!${NC}"
        echo
        echo -e "${CYAN}Your app is available at:${NC}"
        echo -e "${GREEN}https://archon-mcp.fly.dev${NC}"
        ;;
        
    2)
        echo "Which app to replace?"
        read -p "App name: " app_name
        
        echo -e "${YELLOW}Deleting $app_name...${NC}"
        fly apps destroy $app_name -y
        
        echo -e "${GREEN}Creating Archon MCP...${NC}"
        fly launch --name archon-mcp --region fra --no-deploy
        fly deploy
        
        echo -e "${GREEN}✅ Replaced and deployed!${NC}"
        echo -e "${CYAN}https://archon-mcp.fly.dev${NC}"
        ;;
        
    3)
        echo -e "${YELLOW}Cancelled${NC}"
        exit 0
        ;;
esac

echo
echo -e "${GREEN}🎉 Success! Your Archon MCP is live on Fly.io${NC}"
echo
echo -e "${CYAN}Test it:${NC}"
echo "curl https://archon-mcp.fly.dev/health"
echo "curl https://archon-mcp.fly.dev/tools"
echo
echo -e "${CYAN}Manage:${NC}"
echo "fly logs                 # View logs"
echo "fly status              # Check status"
echo "fly ssh console         # SSH into container"
echo
echo -e "${GREEN}NO MORE LOCALHOST! 🚀${NC}"