#!/bin/bash

# ========================================================================
# 🚀 Archon Render Deployment Script
# ========================================================================
# Deploy the multi-agent orchestration system to Render.com
# 
# Prerequisites:
#   - Render CLI installed: brew install render
#   - GitHub repository connected to Render
#   - Render account with billing enabled
# ========================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
RENDER_API_KEY=${RENDER_API_KEY:-""}
GITHUB_REPO=${GITHUB_REPO:-""}
RENDER_OWNER_ID=${RENDER_OWNER_ID:-""}

print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_banner() {
    clear
    print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
    print_color "$CYAN" "║         🚀 ARCHON RENDER DEPLOYMENT SYSTEM 🚀               ║"
    print_color "$CYAN" "║                                                              ║"
    print_color "$CYAN" "║  Deploy to Production Cloud Infrastructure                  ║"
    print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
    echo
}

check_prerequisites() {
    print_color "$YELLOW" "📋 Checking prerequisites..."
    
    # Check Render CLI
    if ! command -v render &> /dev/null; then
        print_color "$RED" "   ❌ Render CLI not installed"
        print_color "$NC" "      Install with: brew install render"
        print_color "$NC" "      Or visit: https://render.com/docs/cli"
        exit 1
    else
        print_color "$GREEN" "   ✅ Render CLI found"
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        print_color "$RED" "   ❌ Git not installed"
        exit 1
    else
        print_color "$GREEN" "   ✅ Git found"
    fi
    
    # Check if in git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_color "$RED" "   ❌ Not in a git repository"
        print_color "$NC" "      Please initialize git: git init"
        exit 1
    else
        print_color "$GREEN" "   ✅ Git repository found"
    fi
    
    print_color "$GREEN" "   ✅ All prerequisites met!\n"
}

setup_render_config() {
    print_color "$YELLOW" "🔧 Setting up Render configuration..."
    
    # Check for render.yaml
    if [ ! -f "render.yaml" ]; then
        print_color "$RED" "   ❌ render.yaml not found"
        exit 1
    else
        print_color "$GREEN" "   ✅ render.yaml found"
    fi
    
    # Interactive setup for Render credentials
    if [ -z "$RENDER_API_KEY" ]; then
        print_color "$CYAN" "\n📝 Render Configuration"
        print_color "$NC" "   Get your API key from: https://dashboard.render.com/account/api-keys"
        read -p "   Render API Key: " RENDER_API_KEY
        export RENDER_API_KEY=$RENDER_API_KEY
    fi
    
    if [ -z "$GITHUB_REPO" ]; then
        # Try to get from git remote
        GITHUB_REPO=$(git config --get remote.origin.url 2>/dev/null || echo "")
        if [ -z "$GITHUB_REPO" ]; then
            read -p "   GitHub Repository URL: " GITHUB_REPO
        else
            print_color "$GREEN" "   ✅ Found GitHub repo: $GITHUB_REPO"
        fi
    fi
    
    print_color "$GREEN" "\n   ✅ Configuration complete!\n"
}

prepare_integrations() {
    print_color "$YELLOW" "📦 Preparing MCP integrations..."
    
    # Create integrations directory
    mkdir -p integrations
    
    # Clone essential MCP repos as submodules or copy
    if [ ! -d "integrations/fastapi-mcp" ]; then
        print_color "$NC" "   Cloning fastapi_mcp..."
        git clone https://github.com/DYAI2025/fastapi_mcp.git integrations/fastapi-mcp 2>/dev/null || true
    fi
    
    if [ ! -d "integrations/git-mcp" ]; then
        print_color "$NC" "   Cloning git-mcp..."
        git clone https://github.com/DYAI2025/git-mcp.git integrations/git-mcp 2>/dev/null || true
    fi
    
    if [ ! -d "integrations/mcp-use" ]; then
        print_color "$NC" "   Cloning mcp-use..."
        git clone https://github.com/DYAI2025/mcp-use.git integrations/mcp-use 2>/dev/null || true
    fi
    
    print_color "$GREEN" "   ✅ Integrations prepared!\n"
}

commit_changes() {
    print_color "$YELLOW" "📝 Committing changes..."
    
    git add -A
    git commit -m "Deploy: Archon multi-agent system to Render with MCP integrations" || true
    
    print_color "$GREEN" "   ✅ Changes committed!\n"
}

deploy_to_render() {
    print_color "$YELLOW" "🚀 Deploying to Render..."
    
    # Push to GitHub
    print_color "$NC" "   Pushing to GitHub..."
    git push origin main || git push origin master
    
    # Create Render blueprint
    print_color "$NC" "   Creating Render services..."
    
    # Use Render CLI or API
    if command -v render &> /dev/null; then
        render up
    else
        print_color "$YELLOW" "   ⚠️  Please complete deployment in Render dashboard:"
        print_color "$NC" "      1. Go to https://dashboard.render.com"
        print_color "$NC" "      2. Click 'New +' → 'Blueprint'"
        print_color "$NC" "      3. Connect your GitHub repo: $GITHUB_REPO"
        print_color "$NC" "      4. Select render.yaml"
        print_color "$NC" "      5. Configure environment variables"
    fi
    
    print_color "$GREEN" "\n   ✅ Deployment initiated!\n"
}

setup_environment_variables() {
    print_color "$YELLOW" "🔐 Environment Variables Setup Required:"
    echo
    print_color "$NC" "   Add these in Render Dashboard → Each Service → Environment:"
    echo
    print_color "$CYAN" "   Required:"
    print_color "$NC" "   • SUPABASE_URL          - Your Supabase project URL"
    print_color "$NC" "   • SUPABASE_SERVICE_KEY  - Your Supabase service key"
    echo
    print_color "$CYAN" "   AI API Keys (at least one):"
    print_color "$NC" "   • OPENAI_API_KEY        - OpenAI API key"
    print_color "$NC" "   • ANTHROPIC_API_KEY     - Anthropic API key"
    print_color "$NC" "   • GOOGLE_API_KEY        - Google AI API key"
    print_color "$NC" "   • XAI_API_KEY           - X.AI API key"
    echo
    print_color "$CYAN" "   Optional:"
    print_color "$NC" "   • GITHUB_TOKEN          - For GitHub integrations"
    print_color "$NC" "   • LOGFIRE_TOKEN         - For monitoring"
    echo
}

estimate_costs() {
    print_color "$CYAN" "💰 Estimated Monthly Costs (Render):"
    echo
    print_color "$NC" "   Core Services:"
    print_color "$NC" "   • Orchestrator (Standard)    - $25/month"
    print_color "$NC" "   • Main Server (Standard)      - $25/month"
    print_color "$NC" "   • MCP Server (Standard)       - $25/month"
    print_color "$NC" "   • Agents Service (Standard)   - $25/month"
    echo
    print_color "$NC" "   Data & Workers:"
    print_color "$NC" "   • Redis (Starter)            - $7/month"
    print_color "$NC" "   • Task Worker (Starter)      - $7/month"
    print_color "$NC" "   • Frontend (Static)          - Free"
    echo
    print_color "$NC" "   Enhanced MCP Services (Optional):"
    print_color "$NC" "   • Git-MCP (Starter)          - $7/month"
    print_color "$NC" "   • Context7 (Starter)         - $7/month"
    print_color "$NC" "   • GitHub-MCP (Starter)       - $7/month"
    echo
    print_color "$YELLOW" "   Base Total: ~$114/month"
    print_color "$YELLOW" "   With all enhancements: ~$135/month"
    echo
    print_color "$GREEN" "   💡 Tip: Start with core services, add enhancements later"
    echo
}

display_next_steps() {
    print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
    print_color "$CYAN" "║                  🎉 DEPLOYMENT INITIATED! 🎉                ║"
    print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
    echo
    
    print_color "$GREEN" "📌 Next Steps:"
    print_color "$NC" "   1. Go to Render Dashboard: https://dashboard.render.com"
    print_color "$NC" "   2. Monitor deployment progress"
    print_color "$NC" "   3. Set environment variables for each service"
    print_color "$NC" "   4. Wait for all services to be 'Live'"
    print_color "$NC" "   5. Access your services at *.onrender.com URLs"
    echo
    
    print_color "$GREEN" "🔗 Service URLs (after deployment):"
    print_color "$NC" "   • Frontend:     https://archon-frontend.onrender.com"
    print_color "$NC" "   • Orchestrator: https://archon-orchestrator.onrender.com"
    print_color "$NC" "   • API Server:   https://archon-server.onrender.com"
    echo
    
    print_color "$GREEN" "📚 Documentation:"
    print_color "$NC" "   • Render Docs: https://render.com/docs"
    print_color "$NC" "   • Blueprint Reference: https://render.com/docs/blueprint-spec"
    echo
}

# Main execution
main() {
    print_banner
    check_prerequisites
    setup_render_config
    prepare_integrations
    commit_changes
    deploy_to_render
    setup_environment_variables
    estimate_costs
    display_next_steps
    
    print_color "$GREEN" "🎊 Render deployment configuration complete!"
    print_color "$CYAN" "   Monitor progress at: https://dashboard.render.com\n"
}

# Handle arguments
case "${1:-}" in
    --help)
        print_banner
        print_color "$GREEN" "Usage: $0 [options]"
        echo
        print_color "$NC" "Deploy Archon multi-agent system to Render.com"
        echo
        print_color "$NC" "Options:"
        print_color "$NC" "  --help     Show this help message"
        print_color "$NC" "  --costs    Show cost breakdown only"
        echo
        print_color "$NC" "Environment Variables:"
        print_color "$NC" "  RENDER_API_KEY    Your Render API key"
        print_color "$NC" "  GITHUB_REPO       GitHub repository URL"
        echo
        exit 0
        ;;
    --costs)
        print_banner
        estimate_costs
        exit 0
        ;;
    *)
        main
        ;;
esac