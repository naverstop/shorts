#!/usr/bin/env python
"""Test trends router import"""

try:
    from app.routes.trends import router
    print(f"✓ Trends router import 성공")
    print(f"  Prefix: {router.prefix}")
    print(f"  Routes: {len(router.routes)}")
    for route in router.routes:
        print(f"    - {route.path} {route.methods}")
except Exception as e:
    print(f"❌ Import 실패: {e}")
    import traceback
    traceback.print_exc()
