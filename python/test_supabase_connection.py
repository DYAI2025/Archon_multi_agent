#!/usr/bin/env python3
"""
Supabase Connection Diagnostic Script

This script tests the Supabase connection and provides detailed information
about what might be wrong with the environment configuration.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_environment_variables():
    """Test if environment variables are properly set."""
    print("🔍 Checking Environment Variables...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url:
        print("❌ SUPABASE_URL is not set")
        return False
    
    if not supabase_key:
        print("❌ SUPABASE_SERVICE_KEY is not set")
        return False
    
    print(f"✅ SUPABASE_URL: {supabase_url[:30]}...")
    print(f"✅ SUPABASE_SERVICE_KEY: {'***' + supabase_key[-4:] if len(supabase_key) > 4 else '***'}")
    
    # Validate URL format
    if not supabase_url.startswith("https://") or not ".supabase.co" in supabase_url:
        print("⚠️  SUPABASE_URL format looks incorrect. Should be: https://your-project.supabase.co")
        return False
    
    # Validate key format (Supabase service keys are typically long JWT tokens)
    if len(supabase_key) < 100:
        print("⚠️  SUPABASE_SERVICE_KEY looks too short. Should be a JWT token.")
        return False
        
    return True

def test_imports():
    """Test if required modules can be imported."""
    print("\n🔍 Testing Python Imports...")
    
    try:
        from supabase import Client, create_client
        print("✅ Supabase library imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import supabase library: {e}")
        print("💡 Try: pip install supabase")
        return False

def test_supabase_connection():
    """Test actual Supabase connection."""
    print("\n🔍 Testing Supabase Connection...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Cannot test connection - missing environment variables")
        return False
    
    try:
        from supabase import create_client
        
        # Try to create client
        client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Try a simple query to test connection
        # This should work with any Supabase project
        result = client.auth.get_user()
        print("✅ Supabase connection test successful")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        print("\n💡 Common issues:")
        print("   - Check if SUPABASE_URL is correct")
        print("   - Check if SUPABASE_SERVICE_KEY is the service_role key (not anon key)")
        print("   - Check if your Supabase project is active")
        print("   - Check internet connection")
        return False

def main():
    """Run all diagnostic tests."""
    print("🚀 Archon Supabase Connection Diagnostic")
    print("=" * 50)
    
    # Load environment variables from .env file if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment variables")
    except Exception as e:
        print(f"⚠️  Could not load .env file: {e}")
    
    all_passed = True
    
    # Test 1: Environment Variables
    if not test_environment_variables():
        all_passed = False
    
    # Test 2: Python Imports
    if not test_imports():
        all_passed = False
        return  # Can't continue without imports
    
    # Test 3: Actual Connection
    if not test_supabase_connection():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Supabase connection is working correctly.")
    else:
        print("💥 Some tests failed. Please check the issues above.")
        
    print("\n📋 Next steps:")
    if not all_passed:
        print("   1. Fix the issues identified above")
        print("   2. Make sure you have a valid Supabase project")
        print("   3. Check the .env.example file for required format")
    else:
        print("   1. Your Supabase connection is working!")
        print("   2. Upload functionality should work correctly")
        print("   3. Check the web UI for any remaining issues")

if __name__ == "__main__":
    main()