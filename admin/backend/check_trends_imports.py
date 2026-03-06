import sys
sys.path.insert(0, 'C:\\shorts\\admin\\backend')

print("1. Testing app.models.trend...")
try:
    from app.models.trend import Trend
    print(f"   ✓ Trend model OK")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n2. Testing app.services.youtube_client...")
try:
    from app.services.youtube_client import YouTubeClient
    print(f"   ✓ YouTubeClient OK")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n3. Testing app.services.gemini_client...")
try:
    from app.services.gemini_client import GeminiClient
    print(f"   ✓ GeminiClient OK")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n4. Testing app.services.trend_service...")
try:
    from app.services.trend_service import TrendService
    print(f"   ✓ TrendService OK")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n5. Testing app.routes.trends...")
try:
    from app.routes.trends import router
    print(f"   ✓ Trends router OK")
    print(f"   Routes: {len(router.routes)}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ All imports successful!" if True else "\n❌ Some imports failed")
