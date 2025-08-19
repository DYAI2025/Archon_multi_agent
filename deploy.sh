#!/bin/bash

# ========================================================================
# 🚀 Archon Multi-Agent Orchestration System - Deployment Script
# ========================================================================
# This script automates the complete setup and deployment of the 
# revolutionary multi-agent AI system that enables Claude Flow, GPT-4, 
# Gemini, Grok, and Claude 3 to work together.
#
# Usage: ./deploy.sh [options]
#   Options:
#     --quick    : Skip interactive setup, use existing .env
#     --test     : Run test after deployment
#     --no-build : Skip Docker build (use existing images)
#     --help     : Show this help message
# ========================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
ENV_EXAMPLE="$SCRIPT_DIR/.env.example"
DOCKER_COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Function: Print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function: Print banner
print_banner() {
    clear
    print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
    print_color "$CYAN" "║       🚀 ARCHON MULTI-AGENT ORCHESTRATION SYSTEM 🚀         ║"
    print_color "$CYAN" "║                                                              ║"
    print_color "$CYAN" "║  Revolutionary AI Collaboration Platform                    ║"
    print_color "$CYAN" "║  Claude Flow + GPT-4 + Gemini + Grok + Claude 3            ║"
    print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
    echo
}

# Function: Check prerequisites
check_prerequisites() {
    print_color "$YELLOW" "📋 Checking prerequisites..."
    
    local missing_deps=0
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_color "$RED" "   ❌ Docker is not installed"
        print_color "$NC" "      Please install Docker from: https://docs.docker.com/get-docker/"
        missing_deps=1
    else
        local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_color "$GREEN" "   ✅ Docker $docker_version found"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_color "$RED" "   ❌ Docker Compose is not installed"
        print_color "$NC" "      Please install Docker Compose from: https://docs.docker.com/compose/install/"
        missing_deps=1
    else
        if docker compose version &> /dev/null; then
            local compose_version=$(docker compose version --short)
        else
            local compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        fi
        print_color "$GREEN" "   ✅ Docker Compose $compose_version found"
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_color "$RED" "   ❌ Docker daemon is not running"
        print_color "$NC" "      Please start Docker Desktop or the Docker service"
        missing_deps=1
    else
        print_color "$GREEN" "   ✅ Docker daemon is running"
    fi
    
    if [ $missing_deps -eq 1 ]; then
        print_color "$RED" "\n❌ Missing prerequisites. Please install required dependencies and try again."
        exit 1
    fi
    
    print_color "$GREEN" "   ✅ All prerequisites met!\n"
}

# Function: Setup environment variables
setup_environment() {
    print_color "$YELLOW" "🔧 Setting up environment variables..."
    
    # Create .env from example if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            print_color "$GREEN" "   ✅ Created .env from .env.example"
        else
            # Create minimal .env file
            cat > "$ENV_FILE" << 'EOF'
# Supabase Configuration (Required)
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# Multi-LLM API Keys (At least one required)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
XAI_API_KEY=
GROQ_API_KEY=

# Model Selection
CODE_AGENT_MODEL=openai:gpt-4o
DOCUMENT_AGENT_MODEL=openai:gpt-4o-mini
RAG_AGENT_MODEL=openai:gpt-4o-mini

# Service Ports
ARCHON_SERVER_PORT=8181
ARCHON_MCP_PORT=8051
ARCHON_AGENTS_PORT=8052
ARCHON_ORCHESTRATOR_PORT=8053
ARCHON_UI_PORT=3737
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO
EOF
            print_color "$GREEN" "   ✅ Created new .env file"
        fi
    else
        print_color "$GREEN" "   ✅ Found existing .env file"
    fi
    
    # Interactive setup for missing API keys (unless --quick flag)
    if [[ ! "$1" == "--quick" ]]; then
        print_color "$CYAN" "\n📝 API Key Configuration"
        print_color "$NC" "   Enter your API keys (press Enter to skip):\n"
        
        # Function to update .env file
        update_env_var() {
            local var_name=$1
            local var_value=$2
            if grep -q "^${var_name}=" "$ENV_FILE"; then
                # Use different sed syntax for macOS vs Linux
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    sed -i '' "s|^${var_name}=.*|${var_name}=${var_value}|" "$ENV_FILE"
                else
                    sed -i "s|^${var_name}=.*|${var_name}=${var_value}|" "$ENV_FILE"
                fi
            else
                echo "${var_name}=${var_value}" >> "$ENV_FILE"
            fi
        }
        
        # Supabase (Required)
        current_supabase_url=$(grep "^SUPABASE_URL=" "$ENV_FILE" | cut -d'=' -f2)
        if [ -z "$current_supabase_url" ]; then
            read -p "   Supabase URL (required): " supabase_url
            if [ ! -z "$supabase_url" ]; then
                update_env_var "SUPABASE_URL" "$supabase_url"
            fi
        fi
        
        current_supabase_key=$(grep "^SUPABASE_SERVICE_KEY=" "$ENV_FILE" | cut -d'=' -f2)
        if [ -z "$current_supabase_key" ]; then
            read -p "   Supabase Service Key (required): " supabase_key
            if [ ! -z "$supabase_key" ]; then
                update_env_var "SUPABASE_SERVICE_KEY" "$supabase_key"
            fi
        fi
        
        # Optional API Keys
        print_color "$NC" "\n   Optional API Keys (at least one recommended):"
        
        current_openai=$(grep "^OPENAI_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
        if [ -z "$current_openai" ]; then
            read -p "   OpenAI API Key (GPT-4): " openai_key
            if [ ! -z "$openai_key" ]; then
                update_env_var "OPENAI_API_KEY" "$openai_key"
            fi
        fi
        
        current_anthropic=$(grep "^ANTHROPIC_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
        if [ -z "$current_anthropic" ]; then
            read -p "   Anthropic API Key (Claude 3): " anthropic_key
            if [ ! -z "$anthropic_key" ]; then
                update_env_var "ANTHROPIC_API_KEY" "$anthropic_key"
            fi
        fi
        
        current_google=$(grep "^GOOGLE_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
        if [ -z "$current_google" ]; then
            read -p "   Google API Key (Gemini): " google_key
            if [ ! -z "$google_key" ]; then
                update_env_var "GOOGLE_API_KEY" "$google_key"
            fi
        fi
        
        current_xai=$(grep "^XAI_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
        if [ -z "$current_xai" ]; then
            read -p "   X.AI API Key (Grok): " xai_key
            if [ ! -z "$xai_key" ]; then
                update_env_var "XAI_API_KEY" "$xai_key"
            fi
        fi
    fi
    
    print_color "$GREEN" "\n   ✅ Environment configuration complete!\n"
}

# Function: Build Docker images
build_docker_images() {
    print_color "$YELLOW" "🔨 Building Docker images..."
    
    if docker compose version &> /dev/null; then
        docker compose build
    else
        docker-compose build
    fi
    
    print_color "$GREEN" "   ✅ Docker images built successfully!\n"
}

# Function: Start services
start_services() {
    print_color "$YELLOW" "🚀 Starting services..."
    
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi
    
    print_color "$GREEN" "   ✅ All services started!\n"
    
    # Show service status
    print_color "$CYAN" "📊 Service Status:"
    if docker compose version &> /dev/null; then
        docker compose ps
    else
        docker-compose ps
    fi
    echo
}

# Function: Wait for services to be healthy
wait_for_services() {
    print_color "$YELLOW" "⏳ Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=0
    local all_healthy=false
    
    while [ $attempt -lt $max_attempts ] && [ "$all_healthy" = false ]; do
        attempt=$((attempt + 1))
        
        # Check each service
        local orchestrator_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8053/health 2>/dev/null || echo "000")
        local server_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8181/health 2>/dev/null || echo "000")
        local agents_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8052/health 2>/dev/null || echo "000")
        
        if [ "$orchestrator_health" = "200" ] && [ "$server_health" = "200" ] && [ "$agents_health" = "200" ]; then
            all_healthy=true
            print_color "$GREEN" "   ✅ All services are healthy!"
        else
            echo -n "."
            sleep 2
        fi
    done
    
    if [ "$all_healthy" = false ]; then
        print_color "$RED" "\n   ⚠️  Some services may not be fully ready yet"
        print_color "$NC" "   You can check logs with: docker-compose logs -f"
    fi
    echo
}

# Function: Display service information
display_service_info() {
    print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
    print_color "$CYAN" "║                    🎉 DEPLOYMENT COMPLETE! 🎉               ║"
    print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
    echo
    
    print_color "$GREEN" "📌 Service Endpoints:"
    print_color "$NC" "   • Frontend UI:        http://localhost:3737"
    print_color "$NC" "   • Orchestrator API:   http://localhost:8053"
    print_color "$NC" "   • Main Server:        http://localhost:8181"
    print_color "$NC" "   • MCP Server:         http://localhost:8051"
    print_color "$NC" "   • Agents Service:     http://localhost:8052"
    print_color "$NC" "   • Redis:              localhost:6379"
    echo
    
    print_color "$GREEN" "🔧 Useful Commands:"
    print_color "$NC" "   • View logs:          docker-compose logs -f"
    print_color "$NC" "   • Stop services:      docker-compose down"
    print_color "$NC" "   • Restart services:   docker-compose restart"
    print_color "$NC" "   • Service status:     docker-compose ps"
    echo
    
    print_color "$GREEN" "📚 Quick Start:"
    print_color "$NC" "   1. Open Frontend:     http://localhost:3737"
    print_color "$NC" "   2. Check API Health:  curl http://localhost:8053/health"
    print_color "$NC" "   3. List Agents:       curl http://localhost:8053/agents"
    print_color "$NC" "   4. Submit Task:       See MULTI_AGENT_README.md for examples"
    echo
}

# Function: Run test
run_test() {
    print_color "$YELLOW" "🧪 Running integration test..."
    
    # Test orchestrator
    response=$(curl -s -X POST http://localhost:8053/test)
    
    if echo "$response" | grep -q "Test orchestration initiated"; then
        print_color "$GREEN" "   ✅ Integration test passed!"
        print_color "$NC" "   Response: $response"
    else
        print_color "$RED" "   ❌ Integration test failed"
        print_color "$NC" "   Response: $response"
    fi
    echo
}

# Function: Show help
show_help() {
    print_banner
    print_color "$GREEN" "Usage: $0 [options]"
    echo
    print_color "$NC" "Options:"
    print_color "$NC" "  --quick    : Skip interactive setup, use existing .env"
    print_color "$NC" "  --test     : Run integration test after deployment"
    print_color "$NC" "  --no-build : Skip Docker build (use existing images)"
    print_color "$NC" "  --help     : Show this help message"
    echo
    print_color "$NC" "Examples:"
    print_color "$NC" "  $0                  # Full interactive setup"
    print_color "$NC" "  $0 --quick          # Quick deployment with existing config"
    print_color "$NC" "  $0 --quick --test   # Quick deployment with test"
    echo
    exit 0
}

# Main execution
main() {
    # Parse arguments
    QUICK_MODE=false
    RUN_TEST=false
    SKIP_BUILD=false
    
    for arg in "$@"; do
        case $arg in
            --quick)
                QUICK_MODE=true
                ;;
            --test)
                RUN_TEST=true
                ;;
            --no-build)
                SKIP_BUILD=true
                ;;
            --help)
                show_help
                ;;
        esac
    done
    
    # Start deployment
    print_banner
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    if [ "$QUICK_MODE" = true ]; then
        setup_environment "--quick"
    else
        setup_environment
    fi
    
    # Build Docker images (unless skipped)
    if [ "$SKIP_BUILD" = false ]; then
        build_docker_images
    fi
    
    # Start services
    start_services
    
    # Wait for services
    wait_for_services
    
    # Run test if requested
    if [ "$RUN_TEST" = true ]; then
        run_test
    fi
    
    # Display service information
    display_service_info
    
    print_color "$GREEN" "🎊 Multi-Agent Orchestration System is ready!"
    print_color "$CYAN" "   Visit http://localhost:3737 to get started\n"
}

# Run main function
main "$@"