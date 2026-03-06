"""Test importing the FastAPI app to check for errors"""
import sys
sys.path.insert(0, 'c:\\shorts\\admin\\backend')

print("1. Importing main app...")
try:
    from app.main import app
    print("✅ Main app imported successfully")
except Exception as e:
    print(f"❌ Error importing main app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n2. Checking routes...")
try:
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"   {route.methods} {route.path}")
    print("✅ Routes loaded successfully")
except Exception as e:
    print(f"❌ Error checking routes: {e}")

print("\n3. Importing auth module directly...")
try:
    from app.routes import auth
    print(f"✅ Auth module imported: {auth}")
    print(f"   Auth router: {auth.router}")
    print(f"   Auth router prefix: {auth.router.prefix}")
except Exception as e:
    print(f"❌ Error importing auth module: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ All imports successful!")
