#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'C:\\shorts\\admin\\backend')

print("1. Testing ScriptService import...")
try:
    from app.services.script_service import ScriptService
    print("   [OK] ScriptService")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing TrendService import...")
try:
    from app.services.trend_service import TrendService
    print("   [OK] TrendService")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing scripts router import...")
try:
    from app.routes.scripts import router as scripts_router
    print(f"   [OK] Scripts router")
    print(f"   Prefix: {scripts_router.prefix}")
    print(f"   Routes: {len(scripts_router.routes)}")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n4. Testing trends router import...")
try:
    from app.routes.trends import router as trends_router
    print(f"   [OK] Trends router")
    print(f"   Prefix: {trends_router.prefix}")
    print(f"   Routes: {len(trends_router.routes)}")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n5. Testing app.routes import...")
try:
    from app.routes import trends_router, scripts_router
    print(f"   [OK] Import from app.routes")
    print(f"   trends_router: {trends_router.prefix}")
    print(f"   scripts_router: {scripts_router.prefix}")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")
