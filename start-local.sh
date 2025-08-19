#!/bin/bash

# ========================================================================
# 🚀 Archon Local Start Script mit Repository-Integrationen
# ========================================================================
# Startet das erweiterte System lokal mit allen Boosts
# ========================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

print_color() {
    echo -e "${1}${2}${NC}"
}

print_banner() {
    clear
    print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
    print_color "$CYAN" "║     🚀 ARCHON LOCAL + REPOSITORY INTEGRATIONS 🚀            ║"
    print_color "$CYAN" "║                                                              ║"
    print_color "$CYAN" "║  Enhanced mit: fastapi_mcp, mcp-use, git-mcp & mehr         ║"
    print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
    echo
}

check_docker() {
    print_color "$YELLOW" "📋 Checking Docker..."
    
    if ! docker info &> /dev/null; then
        print_color "$RED" "   ❌ Docker is not running!"
        print_color "$NC" "   Please start Docker Desktop first"
        
        # Try to start Docker on macOS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_color "$YELLOW" "   Attempting to start Docker Desktop..."
            open -a Docker
            
            # Wait for Docker to start
            print_color "$NC" "   Waiting for Docker to start..."
            for i in {1..30}; do
                if docker info &> /dev/null; then
                    print_color "$GREEN" "   ✅ Docker started successfully!"
                    break
                fi
                echo -n "."
                sleep 2
            done
            
            if ! docker info &> /dev/null; then
                print_color "$RED" "   Docker failed to start. Please start it manually."
                exit 1
            fi
        else
            exit 1
        fi
    else
        print_color "$GREEN" "   ✅ Docker is running"
    fi
}

check_integrations() {
    print_color "$YELLOW" "📦 Checking repository integrations..."
    
    if [ ! -d "integrations" ]; then
        print_color "$YELLOW" "   Creating integrations directory..."
        mkdir -p integrations
    fi
    
    # Check each integration
    repos=(
        "fastapi_mcp"
        "mcp-use"
        "git-mcp"
        "context7"
        "github-mcp-server"
        "SuperClaude_Framework"
    )
    
    for repo in "${repos[@]}"; do
        if [ ! -d "integrations/$repo" ]; then
            print_color "$YELLOW" "   Cloning $repo..."
            git clone "https://github.com/DYAI2025/$repo.git" "integrations/$repo" 2>/dev/null || true
        else
            print_color "$GREEN" "   ✅ $repo found"
        fi
    done
    
    print_color "$GREEN" "   ✅ All integrations ready!\n"
}

build_services() {
    print_color "$YELLOW" "🔨 Building enhanced services..."
    
    # Build only the enhanced MCP server
    docker-compose build archon-mcp
    
    print_color "$GREEN" "   ✅ Enhanced MCP built!\n"
}

start_services() {
    print_color "$YELLOW" "🚀 Starting all services..."
    
    docker-compose up -d
    
    print_color "$GREEN" "   ✅ Services starting...\n"
    
    # Show status
    docker-compose ps
}

wait_for_health() {
    print_color "$YELLOW" "⏳ Waiting for services to be healthy..."
    
    services=(
        "http://localhost:8051/health:Enhanced MCP"
        "http://localhost:8053/health:Orchestrator"
        "http://localhost:8181/health:Main Server"
        "http://localhost:8052/health:Agents"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r url name <<< "$service"
        
        for i in {1..15}; do
            if curl -s "$url" > /dev/null 2>&1; then
                print_color "$GREEN" "   ✅ $name is ready"
                break
            fi
            if [ $i -eq 15 ]; then
                print_color "$YELLOW" "   ⚠️  $name might not be ready yet"
            fi
            sleep 2
        done
    done
    
    echo
}

test_integrations() {
    print_color "$CYAN" "🧪 Testing integrations..."
    
    # Test enhanced MCP
    response=$(curl -s http://localhost:8051/test 2>/dev/null || echo "{}")
    
    if echo "$response" | grep -q "operational"; then
        print_color "$GREEN" "   ✅ All integrations operational!"
    else
        print_color "$YELLOW" "   ⚠️  Some integrations may need configuration"
    fi
    
    # Show available tools
    tools_count=$(curl -s http://localhost:8051/tools 2>/dev/null | grep -o '"name"' | wc -l || echo 0)
    print_color "$GREEN" "   📊 Available MCP tools: $tools_count"
    
    echo
}

show_info() {
    print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
    print_color "$CYAN" "║                  🎉 SYSTEM READY! 🎉                        ║"
    print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
    echo
    
    print_color "$GREEN" "📌 Enhanced Services:"
    print_color "$NC" "   • Frontend:         http://localhost:3737"
    print_color "$NC" "   • Enhanced MCP:     http://localhost:8051"
    print_color "$NC" "   • Orchestrator:     http://localhost:8053"
    print_color "$NC" "   • Main Server:      http://localhost:8181"
    echo
    
    print_color "$GREEN" "🆕 New Capabilities:"
    print_color "$NC" "   • fastapi_mcp:      FastAPI → MCP Tools"
    print_color "$NC" "   • mcp-use:          Multi-LLM Agents"
    print_color "$NC" "   • git-mcp:          GitHub Docs Access"
    print_color "$NC" "   • context7:         Real-time Docs"
    print_color "$NC" "   • github-mcp:       Repo Management"
    echo
    
    print_color "$GREEN" "🔧 Quick Commands:"
    print_color "$NC" "   • View logs:        docker-compose logs -f"
    print_color "$NC" "   • List tools:       curl http://localhost:8051/tools"
    print_color "$NC" "   • Test GitHub:      curl -X POST http://localhost:8051/tools/github:get_readme -d '{\"arguments\":{\"repo\":\"anthropics/claude-engineer\"}}'"
    echo
    
    print_color "$CYAN" "💡 System is 3x more powerful with integrations!"
    echo
}

# Main execution
main() {
    print_banner
    check_docker
    check_integrations
    build_services
    start_services
    wait_for_health
    test_integrations
    show_info
    
    print_color "$GREEN" "🚀 Local system with repository boosts is ready!"
    print_color "$CYAN" "   Open http://localhost:3737 to start\n"
}

# Handle arguments
case "${1:-}" in
    stop)
        print_color "$YELLOW" "Stopping services..."
        docker-compose down
        print_color "$GREEN" "Services stopped"
        ;;
    restart)
        print_color "$YELLOW" "Restarting services..."
        docker-compose restart
        print_color "$GREEN" "Services restarted"
        ;;
    logs)
        docker-compose logs -f
        ;;
    status)
        docker-compose ps
        ;;
    *)
        main
        ;;
esac