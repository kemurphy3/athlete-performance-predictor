#!/usr/bin/env python3
"""
Test script for the multi-tenant fitness platform API
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all API modules can be imported"""
    try:
        print("🔍 Testing API imports...")
        
        # Test core modules
        from src.auth import AuthManager, OAuthManager
        print("✅ Auth modules imported successfully")
        
        from src.auth.models import User, UserCreate, UserLogin
        print("✅ Auth models imported successfully")
        
        # Test API modules
        from src.api import app
        print("✅ Main API app imported successfully")
        
        from src.api.auth import router as auth_router
        print("✅ Auth router imported successfully")
        
        from src.api.sources import router as sources_router
        print("✅ Sources router imported successfully")
        
        from src.api.workouts import router as workouts_router
        print("✅ Workouts router imported successfully")
        
        from src.api.biometrics import router as biometrics_router
        print("✅ Biometrics router imported successfully")
        
        from src.api.analysis import router as analysis_router
        print("✅ Analysis router imported successfully")
        
        from src.api.chat import router as chat_router
        print("✅ Chat router imported successfully")
        
        from src.api.export import router as export_router
        print("✅ Export router imported successfully")
        
        print("\n🎉 All API modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_structure():
    """Test the API structure and routes"""
    try:
        print("\n🔍 Testing API structure...")
        
        from src.api import app
        
        # Check that all routers are included
        routes = [route.path for route in app.routes]
        
        expected_prefixes = [
            "/auth",
            "/api/sources", 
            "/api/workouts",
            "/api/biometrics",
            "/api/analysis",
            "/api/chat",
            "/api/export"
        ]
        
        for prefix in expected_prefixes:
            matching_routes = [r for r in routes if r.startswith(prefix)]
            if matching_routes:
                print(f"✅ {prefix} routes found: {len(matching_routes)} routes")
            else:
                print(f"❌ {prefix} routes not found")
                return False
        
        # Check health endpoint
        if "/health" in routes:
            print("✅ Health endpoint found")
        else:
            print("❌ Health endpoint not found")
            return False
        
        print("\n🎉 API structure test passed!")
        return True
        
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False

def test_auth_manager():
    """Test basic auth manager functionality"""
    try:
        print("\n🔍 Testing Auth Manager...")
        
        from src.auth import AuthManager
        import uuid
        
        # Initialize auth manager with the same database we migrated
        auth_manager = AuthManager("data/athlete_performance.db")
        print("✅ Auth manager initialized")
        
        # Test user creation with unique email
        from src.auth.models import UserCreate, UserRole
        
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = UserCreate(
            email=unique_email,
            password="testpassword123",
            first_name="Test",
            last_name="User",
            role=UserRole.USER
        )
        
        user = auth_manager.create_user(user_data)
        print(f"✅ User created: {user.email}")
        
        # Test user retrieval
        retrieved_user = auth_manager.get_user_by_email(unique_email)
        if retrieved_user and retrieved_user.email == unique_email:
            print("✅ User retrieval works")
        else:
            print("❌ User retrieval failed")
            return False
        
        print("\n🎉 Auth Manager test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Auth Manager test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Multi-Tenant Fitness Platform API")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_api_structure,
        test_auth_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
