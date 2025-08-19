#!/usr/bin/env python3
"""
🚀 Archon Multi-Agent Orchestration System - Deployment Script (Python)

Cross-platform deployment script for the revolutionary multi-agent AI system
that enables Claude Flow, GPT-4, Gemini, Grok, and Claude 3 to work together.

Usage:
    python deploy.py [options]
    
Options:
    --quick    : Skip interactive setup, use existing .env
    --test     : Run integration test after deployment
    --no-build : Skip Docker build (use existing images)
    --help     : Show help message
"""

import os
import sys
import subprocess
import time
import argparse
import platform
from pathlib import Path
import shutil
import json

try:
    import requests
except ImportError:
    print("Installing requests library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color
    
    @staticmethod
    def supported():
        """Check if terminal supports colors."""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    @staticmethod
    def print(color, *args):
        """Print with color if supported."""
        if Colors.supported():
            print(f"{color}{' '.join(str(arg) for arg in args)}{Colors.NC}")
        else:
            print(*args)


class DeploymentManager:
    """Manages the deployment of the Archon Multi-Agent System."""
    
    def __init__(self, quick_mode=False, run_test=False, skip_build=False):
        self.quick_mode = quick_mode
        self.run_test = run_test
        self.skip_build = skip_build
        self.script_dir = Path(__file__).parent.absolute()
        self.env_file = self.script_dir / ".env"
        self.env_example = self.script_dir / ".env.example"
        self.docker_compose_file = self.script_dir / "docker-compose.yml"
        
    def print_banner(self):
        """Print the deployment banner."""
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')
            
        Colors.print(Colors.CYAN, "╔══════════════════════════════════════════════════════════════╗")
        Colors.print(Colors.CYAN, "║       🚀 ARCHON MULTI-AGENT ORCHESTRATION SYSTEM 🚀         ║")
        Colors.print(Colors.CYAN, "║                                                              ║")
        Colors.print(Colors.CYAN, "║  Revolutionary AI Collaboration Platform                    ║")
        Colors.print(Colors.CYAN, "║  Claude Flow + GPT-4 + Gemini + Grok + Claude 3            ║")
        Colors.print(Colors.CYAN, "╚══════════════════════════════════════════════════════════════╝")
        print()
        
    def check_command(self, command):
        """Check if a command is available."""
        return shutil.which(command) is not None
    
    def run_command(self, command, capture=False, shell=True):
        """Run a shell command."""
        try:
            if capture:
                result = subprocess.run(
                    command, 
                    shell=shell, 
                    capture_output=True, 
                    text=True,
                    check=False
                )
                return result.returncode == 0, result.stdout.strip()
            else:
                return subprocess.run(command, shell=shell, check=False).returncode == 0, None
        except Exception as e:
            return False, str(e)
    
    def check_prerequisites(self):
        """Check if all prerequisites are installed."""
        Colors.print(Colors.YELLOW, "📋 Checking prerequisites...")
        
        missing_deps = False
        
        # Check Docker
        if not self.check_command("docker"):
            Colors.print(Colors.RED, "   ❌ Docker is not installed")
            print("      Please install Docker from: https://docs.docker.com/get-docker/")
            missing_deps = True
        else:
            success, version = self.run_command("docker --version", capture=True)
            if success:
                Colors.print(Colors.GREEN, f"   ✅ Docker found: {version}")
            else:
                Colors.print(Colors.RED, "   ❌ Docker found but cannot get version")
                missing_deps = True
        
        # Check Docker Compose
        compose_v2 = self.run_command("docker compose version", capture=True)[0]
        compose_v1 = self.check_command("docker-compose")
        
        if not compose_v2 and not compose_v1:
            Colors.print(Colors.RED, "   ❌ Docker Compose is not installed")
            print("      Please install Docker Compose from: https://docs.docker.com/compose/install/")
            missing_deps = True
        else:
            if compose_v2:
                success, version = self.run_command("docker compose version --short", capture=True)
                Colors.print(Colors.GREEN, f"   ✅ Docker Compose v2 found: {version}")
            else:
                success, version = self.run_command("docker-compose --version", capture=True)
                Colors.print(Colors.GREEN, f"   ✅ Docker Compose v1 found: {version}")
        
        # Check if Docker daemon is running
        success, _ = self.run_command("docker info", capture=True)
        if not success:
            Colors.print(Colors.RED, "   ❌ Docker daemon is not running")
            if platform.system() == "Windows":
                print("      Please start Docker Desktop")
            else:
                print("      Please start Docker Desktop or the Docker service")
            missing_deps = True
        else:
            Colors.print(Colors.GREEN, "   ✅ Docker daemon is running")
        
        if missing_deps:
            Colors.print(Colors.RED, "\n❌ Missing prerequisites. Please install required dependencies and try again.")
            sys.exit(1)
        
        Colors.print(Colors.GREEN, "   ✅ All prerequisites met!\n")
    
    def setup_environment(self):
        """Setup environment variables."""
        Colors.print(Colors.YELLOW, "🔧 Setting up environment variables...")
        
        # Create .env from example if it doesn't exist
        if not self.env_file.exists():
            if self.env_example.exists():
                shutil.copy(self.env_example, self.env_file)
                Colors.print(Colors.GREEN, "   ✅ Created .env from .env.example")
            else:
                # Create minimal .env file
                env_content = """# Supabase Configuration (Required)
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
"""
                with open(self.env_file, 'w') as f:
                    f.write(env_content)
                Colors.print(Colors.GREEN, "   ✅ Created new .env file")
        else:
            Colors.print(Colors.GREEN, "   ✅ Found existing .env file")
        
        # Interactive setup for missing API keys (unless --quick flag)
        if not self.quick_mode:
            self.interactive_setup()
        
        Colors.print(Colors.GREEN, "\n   ✅ Environment configuration complete!\n")
    
    def interactive_setup(self):
        """Interactive setup for API keys."""
        Colors.print(Colors.CYAN, "\n📝 API Key Configuration")
        print("   Enter your API keys (press Enter to skip):\n")
        
        # Read current .env file
        env_vars = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
        
        # Function to update environment variable
        def update_env_var(var_name, var_value):
            env_vars[var_name] = var_value
        
        # Supabase (Required)
        if not env_vars.get('SUPABASE_URL'):
            supabase_url = input("   Supabase URL (required): ").strip()
            if supabase_url:
                update_env_var('SUPABASE_URL', supabase_url)
        
        if not env_vars.get('SUPABASE_SERVICE_KEY'):
            supabase_key = input("   Supabase Service Key (required): ").strip()
            if supabase_key:
                update_env_var('SUPABASE_SERVICE_KEY', supabase_key)
        
        # Optional API Keys
        print("\n   Optional API Keys (at least one recommended):")
        
        if not env_vars.get('OPENAI_API_KEY'):
            openai_key = input("   OpenAI API Key (GPT-4): ").strip()
            if openai_key:
                update_env_var('OPENAI_API_KEY', openai_key)
        
        if not env_vars.get('ANTHROPIC_API_KEY'):
            anthropic_key = input("   Anthropic API Key (Claude 3): ").strip()
            if anthropic_key:
                update_env_var('ANTHROPIC_API_KEY', anthropic_key)
        
        if not env_vars.get('GOOGLE_API_KEY'):
            google_key = input("   Google API Key (Gemini): ").strip()
            if google_key:
                update_env_var('GOOGLE_API_KEY', google_key)
        
        if not env_vars.get('XAI_API_KEY'):
            xai_key = input("   X.AI API Key (Grok): ").strip()
            if xai_key:
                update_env_var('XAI_API_KEY', xai_key)
        
        # Write updated .env file
        with open(self.env_file, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
    
    def build_docker_images(self):
        """Build Docker images."""
        if self.skip_build:
            Colors.print(Colors.YELLOW, "⏩ Skipping Docker build (--no-build flag)")
            return
        
        Colors.print(Colors.YELLOW, "🔨 Building Docker images...")
        
        # Determine which docker-compose command to use
        compose_cmd = "docker compose" if self.run_command("docker compose version", capture=True)[0] else "docker-compose"
        
        success, _ = self.run_command(f"{compose_cmd} build")
        if success:
            Colors.print(Colors.GREEN, "   ✅ Docker images built successfully!\n")
        else:
            Colors.print(Colors.RED, "   ❌ Failed to build Docker images")
            sys.exit(1)
    
    def start_services(self):
        """Start all services."""
        Colors.print(Colors.YELLOW, "🚀 Starting services...")
        
        # Determine which docker-compose command to use
        compose_cmd = "docker compose" if self.run_command("docker compose version", capture=True)[0] else "docker-compose"
        
        success, _ = self.run_command(f"{compose_cmd} up -d")
        if success:
            Colors.print(Colors.GREEN, "   ✅ All services started!\n")
        else:
            Colors.print(Colors.RED, "   ❌ Failed to start services")
            sys.exit(1)
        
        # Show service status
        Colors.print(Colors.CYAN, "📊 Service Status:")
        self.run_command(f"{compose_cmd} ps")
        print()
    
    def wait_for_services(self):
        """Wait for services to be healthy."""
        Colors.print(Colors.YELLOW, "⏳ Waiting for services to be healthy...")
        
        max_attempts = 30
        attempt = 0
        all_healthy = False
        
        while attempt < max_attempts and not all_healthy:
            attempt += 1
            
            try:
                # Check each service
                orchestrator_health = requests.get("http://localhost:8053/health", timeout=2).status_code == 200
                server_health = requests.get("http://localhost:8181/health", timeout=2).status_code == 200
                agents_health = requests.get("http://localhost:8052/health", timeout=2).status_code == 200
                
                if orchestrator_health and server_health and agents_health:
                    all_healthy = True
                    Colors.print(Colors.GREEN, "   ✅ All services are healthy!")
                else:
                    print(".", end="", flush=True)
                    time.sleep(2)
            except:
                print(".", end="", flush=True)
                time.sleep(2)
        
        if not all_healthy:
            Colors.print(Colors.RED, "\n   ⚠️  Some services may not be fully ready yet")
            print("   You can check logs with: docker-compose logs -f")
        print()
    
    def run_test(self):
        """Run integration test."""
        Colors.print(Colors.YELLOW, "🧪 Running integration test...")
        
        try:
            response = requests.post("http://localhost:8053/test", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if "Test orchestration initiated" in str(result):
                    Colors.print(Colors.GREEN, "   ✅ Integration test passed!")
                    print(f"   Response: {json.dumps(result, indent=2)}")
                else:
                    Colors.print(Colors.RED, "   ❌ Integration test failed")
                    print(f"   Response: {result}")
            else:
                Colors.print(Colors.RED, f"   ❌ Integration test failed with status {response.status_code}")
        except Exception as e:
            Colors.print(Colors.RED, f"   ❌ Integration test failed: {e}")
        print()
    
    def display_service_info(self):
        """Display service information."""
        Colors.print(Colors.CYAN, "╔══════════════════════════════════════════════════════════════╗")
        Colors.print(Colors.CYAN, "║                    🎉 DEPLOYMENT COMPLETE! 🎉               ║")
        Colors.print(Colors.CYAN, "╚══════════════════════════════════════════════════════════════╝")
        print()
        
        Colors.print(Colors.GREEN, "📌 Service Endpoints:")
        print("   • Frontend UI:        http://localhost:3737")
        print("   • Orchestrator API:   http://localhost:8053")
        print("   • Main Server:        http://localhost:8181")
        print("   • MCP Server:         http://localhost:8051")
        print("   • Agents Service:     http://localhost:8052")
        print("   • Redis:              localhost:6379")
        print()
        
        Colors.print(Colors.GREEN, "🔧 Useful Commands:")
        compose_cmd = "docker compose" if self.run_command("docker compose version", capture=True)[0] else "docker-compose"
        print(f"   • View logs:          {compose_cmd} logs -f")
        print(f"   • Stop services:      {compose_cmd} down")
        print(f"   • Restart services:   {compose_cmd} restart")
        print(f"   • Service status:     {compose_cmd} ps")
        print()
        
        Colors.print(Colors.GREEN, "📚 Quick Start:")
        print("   1. Open Frontend:     http://localhost:3737")
        print("   2. Check API Health:  curl http://localhost:8053/health")
        print("   3. List Agents:       curl http://localhost:8053/agents")
        print("   4. Submit Task:       See MULTI_AGENT_README.md for examples")
        print()
    
    def deploy(self):
        """Main deployment process."""
        self.print_banner()
        self.check_prerequisites()
        self.setup_environment()
        self.build_docker_images()
        self.start_services()
        self.wait_for_services()
        
        if self.run_test:
            self.run_test()
        
        self.display_service_info()
        
        Colors.print(Colors.GREEN, "🎊 Multi-Agent Orchestration System is ready!")
        Colors.print(Colors.CYAN, "   Visit http://localhost:3737 to get started\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deploy the Archon Multi-Agent Orchestration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy.py                  # Full interactive setup
  python deploy.py --quick          # Quick deployment with existing config
  python deploy.py --quick --test   # Quick deployment with test
        """
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Skip interactive setup, use existing .env'
    )
    parser.add_argument(
        '--test', 
        action='store_true',
        help='Run integration test after deployment'
    )
    parser.add_argument(
        '--no-build', 
        action='store_true',
        help='Skip Docker build (use existing images)'
    )
    
    args = parser.parse_args()
    
    # Create and run deployment manager
    manager = DeploymentManager(
        quick_mode=args.quick,
        run_test=args.test,
        skip_build=args.no_build
    )
    
    try:
        manager.deploy()
    except KeyboardInterrupt:
        Colors.print(Colors.YELLOW, "\n\n⚠️  Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        Colors.print(Colors.RED, f"\n❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()