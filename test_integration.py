#!/usr/bin/env python3
"""
Integration test script for Archon multi-agent system with Supabase.

This script tests the core functionality to ensure everything is working properly.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_backend_health():
    """Test if the backend server is responding correctly."""
    print("🔍 Testing backend health...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8181/health", timeout=5.0)
            data = response.json()
            
            print(f"✅ Backend server status: {data['status']}")
            print(f"✅ Backend ready: {data['ready']}")
            print(f"✅ Initialization complete: {data['initialization_complete']}")
            
            if data['status'] in ['healthy', 'degraded']:
                print("✅ Backend server is running correctly")
                return True
            else:
                print(f"❌ Backend server status: {data['status']}")
                return False
                
    except Exception as e:
        print(f"❌ Backend server test failed: {e}")
        return False

async def test_frontend_availability():
    """Test if the frontend is accessible."""
    print("🔍 Testing frontend availability...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:5173/", timeout=5.0)
            
            if response.status_code == 200 and "html" in response.text.lower():
                print("✅ Frontend is accessible")
                return True
            else:
                print(f"❌ Frontend response: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

async def test_mcp_integrations():
    """Test if MCP integrations are properly loaded."""
    print("🔍 Testing MCP integrations...")
    
    try:
        # Test if the enhanced MCP server can be imported
        python_path = Path(__file__).parent / "python"
        result = subprocess.run([
            sys.executable, "-c", 
            "from src.mcp.enhanced_server import EnhancedMCPServer; print('MCP integrations loaded')"
        ], cwd=python_path, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Enhanced MCP server can be imported")
            print(f"   Output: {result.stdout.strip()}")
            if result.stderr:
                print(f"   Warnings: {result.stderr.strip()}")
            return True
        else:
            print(f"❌ MCP integration import failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP integration test failed: {e}")
        return False

def test_environment_configuration():
    """Test if environment variables are properly configured."""
    print("🔍 Testing environment configuration...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if supabase_url and supabase_key:
        print(f"✅ SUPABASE_URL: {supabase_url[:30]}...")
        print(f"✅ SUPABASE_SERVICE_KEY: {'***' + supabase_key[-4:] if len(supabase_key) > 4 else '***'}")
        
        if "example.supabase.co" in supabase_url:
            print("⚠️  Using placeholder Supabase URL - update with real credentials for full functionality")
        
        return True
    else:
        print("❌ Missing Supabase configuration")
        return False

def test_integration_dependencies():
    """Test if integration dependencies are available."""
    print("🔍 Testing integration dependencies...")
    
    integrations = [
        "fastapi_mcp",
        "mcp-use", 
        "Gitingest-MCP"
    ]
    
    integrations_path = Path(__file__).parent / "integrations"
    available = []
    
    for integration in integrations:
        path = integrations_path / integration
        if path.exists():
            available.append(integration)
            print(f"✅ {integration} integration available")
        else:
            print(f"❌ {integration} integration missing")
    
    if len(available) >= 2:  # At least 2 out of 3 integrations
        print(f"✅ {len(available)}/3 integrations available")
        return True
    else:
        print(f"❌ Only {len(available)}/3 integrations available")
        return False

async def main():
    """Run all integration tests."""
    print("🚀 Archon Multi-Agent Integration Test")
    print("=" * 50)
    
    tests = [
        ("Environment Configuration", test_environment_configuration),
        ("Integration Dependencies", test_integration_dependencies),
        ("MCP Integrations", test_mcp_integrations),
        ("Backend Health", test_backend_health),
        ("Frontend Availability", test_frontend_availability),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * len(test_name))
        
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Archon is ready to use.")
    elif passed >= len(results) - 1:
        print("⚠️  Most tests passed. Minor issues detected but system should work.")
    else:
        print("❌ Multiple test failures. Please check the configuration.")
    
    return passed >= len(results) - 1

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)