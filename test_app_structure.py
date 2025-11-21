#!/usr/bin/env python3
"""
Simple test script to verify app structure without running the server.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing KIVI Backend structure...")
print("=" * 60)

# Test 1: Import main app
try:
    print("1. Importing FastAPI app...")
    from app.main import app
    print("   ✓ FastAPI app imported successfully")
    print(f"   ✓ App title: {app.title}")
    print(f"   ✓ Total routes: {len(app.routes)}")
except Exception as e:
    print(f"   ✗ Failed to import app: {e}")
    sys.exit(1)

# Test 2: Check route modules
try:
    print("\n2. Checking route modules...")
    from app.api.v1 import routes_auth, routes_user, routes_finance, routes_whatsapp, routes_ai
    print("   ✓ All route modules imported")
    print(f"   ✓ Auth routes: {len(routes_auth.router.routes)}")
    print(f"   ✓ User routes: {len(routes_user.router.routes)}")
    print(f"   ✓ Finance routes: {len(routes_finance.router.routes)}")
    print(f"   ✓ WhatsApp routes: {len(routes_whatsapp.router.routes)}")
    print(f"   ✓ AI routes: {len(routes_ai.router.routes)}")
except Exception as e:
    print(f"   ✗ Failed to import route modules: {e}")
    sys.exit(1)

# Test 3: Check core modules
try:
    print("\n3. Checking core modules...")
    from app.core import security, exceptions
    from app.config import config, logging_config
    from app.db import mongodb
    print("   ✓ Core modules imported")
except Exception as e:
    print(f"   ✗ Failed to import core modules: {e}")
    sys.exit(1)

# Test 4: Check service modules
try:
    print("\n4. Checking service modules...")
    from app.services import (
        ai_chat,
        whatsapp_service,
        sms_parser,
        expense_analyzer,
        nudge_engine,
        aa_service
    )
    print("   ✓ Service modules imported")
except Exception as e:
    print(f"   ✗ Failed to import service modules: {e}")
    sys.exit(1)

# Test 5: Check model modules
try:
    print("\n5. Checking model modules...")
    from app.models import (
        user_model,
        transaction_model,
        message_log_model,
        session_model
    )
    print("   ✓ Model modules imported")
except Exception as e:
    print(f"   ✗ Failed to import model modules: {e}")
    sys.exit(1)

# Test 6: List all endpoints
print("\n6. Available endpoints:")
print("   " + "-" * 56)
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        methods = ', '.join(route.methods)
        print(f"   {methods:10} {route.path}")
print("   " + "-" * 56)

print("\n" + "=" * 60)
print("✓ All tests passed! KIVI Backend structure is valid.")
print("=" * 60)
print("\nTo run the server:")
print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
print("\nAPI Documentation:")
print("  http://localhost:8000/docs")
print("  http://localhost:8000/redoc")
