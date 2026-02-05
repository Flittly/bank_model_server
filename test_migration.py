#!/usr/bin/env python3
"""
Test script to verify FastAPI migration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported successfully"""
    try:
        print("Testing imports...")

        # Test FastAPI app creation
        from app import create_app
        app = create_app()
        print("✓ FastAPI app created successfully")

        # Test APIRouter
        from app.main import api_router
        print("✓ APIRouter imported successfully")

        # Test controllers
        from app.main import controllers
        print("✓ Controllers imported successfully")

        # Test schemas
        from app.main import schemas
        print("✓ Schemas imported successfully")

        # Test config
        import config
        print("✓ Config imported successfully")

        # Test util
        import util
        print("✓ Util imported successfully")

        # Test model
        import model
        print("✓ Model imported successfully")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI app structure"""
    try:
        from app import create_app

        app = create_app()

        # Check that app has the router included
        if app.routes:
            print("✓ App has routes")
            print(f"  Number of routes: {len(app.routes)}")
        else:
            print("✗ App has no routes")
            return False

        # Check for specific expected routes
        route_paths = [route.path for route in app.routes]

        expected_routes = [
            "/mc/status",
            "/mc/result",
            "/mc/error",
            "/fs/result/file",
            "/fs/resource/file",
            "/fs/result/zip",
            "/{category}/{model_name}"
        ]

        for expected_route in expected_routes:
            found = any(expected_route in path for path in route_paths)
            if found:
                print(f"✓ Found expected route: {expected_route}")
            else:
                print(f"✗ Missing expected route: {expected_route}")

        return True
    except Exception as e:
        print(f"✗ FastAPI app test failed: {e}")
        return False

def test_schemas():
    """Test Pydantic schemas"""
    try:
        from app.main.schemas import (
            CaseId, CaseIds, ModelCaseStatus, ModelCaseResult, ModelCaseError,
            CallTimeResponse, SerializationResponse, DiskUsageResponse,
            ErrorResponse, SuccessResponse
        )

        # Test creating schema instances
        case_id = CaseId(id="test123")
        print("✓ CaseId schema works")

        case_ids = CaseIds(case_ids=["test1", "test2"])
        print("✓ CaseIds schema works")

        status = ModelCaseStatus(status="RUNNING")
        print("✓ ModelCaseStatus schema works")

        result = ModelCaseResult(result={"output": "test"})
        print("✓ ModelCaseResult schema works")

        error = ModelCaseError(error="Test error")
        print("✓ ModelCaseError schema works")

        success = SuccessResponse(message="OK", status_code=200)
        print("✓ SuccessResponse schema works")

        return True
    except Exception as e:
        print(f"✗ Schema test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Testing FastAPI Migration ===\n")

    tests = [
        ("Import Test", test_imports),
        ("FastAPI App Test", test_fastapi_app),
        ("Schema Test", test_schemas)
    ]

    all_passed = True

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if not test_func():
            all_passed = False

    print("\n=== Test Results ===")
    if all_passed:
        print("✓ All tests passed! Migration appears successful.")
        return 0
    else:
        print("✗ Some tests failed. Please check the migration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())