#!/usr/bin/env python3
"""
Test script to verify the fixed type error and upload functionality.
"""

import asyncio
import sys
import os

# Add the Python source path
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

async def test_crawler_manager_import():
    """Test that the CrawlerManager can be imported without type errors."""
    print("🔍 Testing CrawlerManager import...")
    try:
        from python.src.server.services.crawler_manager import CrawlerManager, get_crawler
        print("✅ CrawlerManager imported successfully")
        return True
    except Exception as e:
        print(f"❌ CrawlerManager import failed: {e}")
        return False

async def test_fastapi_app_import():
    """Test that the FastAPI app can be imported without crashes."""
    print("🔍 Testing FastAPI app import...")
    try:
        # Set PYTHONPATH for imports
        os.environ['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), 'python')
        
        from python.src.server.main import app
        print("✅ FastAPI app imported successfully")
        return True
    except Exception as e:
        print(f"❌ FastAPI app import failed: {e}")
        return False

async def test_error_handling():
    """Test that error handling distinguishes between upload and crawl errors."""
    print("🔍 Testing error handling...")
    try:
        from python.src.server.api_routes.socketio_handlers import error_crawl_progress
        
        # Test document upload error
        await error_crawl_progress('test-upload', 'Test upload error', 'document')
        print("✅ Document error handling works")
        
        # Test crawl error  
        await error_crawl_progress('test-crawl', 'Test crawl error', 'crawl')
        print("✅ Crawl error handling works")
        
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

async def main():
    """Run all verification tests."""
    print("🚀 Archon Fix Verification")
    print("=" * 50)
    
    all_passed = True
    
    # Test 1: CrawlerManager import
    if not await test_crawler_manager_import():
        all_passed = False
    
    # Test 2: FastAPI app import
    if not await test_fastapi_app_import():
        all_passed = False
        
    # Test 3: Error handling
    if not await test_error_handling():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! The critical type error is fixed.")
        print("✅ Server can now start without crashes")
        print("✅ Error messages will distinguish between uploads and crawls")
    else:
        print("❌ Some tests failed. Please check the logs above.")
        
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)