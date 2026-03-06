import sys
sys.path.insert(0, 'C:\\shorts\\admin\\backend')

print("Testing app.routes import...")
try:
    from app.routes import trends_router, scripts_router, upload_quotas_router
    print(f"✓ trends_router: {trends_router.prefix}")
    print(f"✓ scripts_router: {scripts_router.prefix}")
    print(f"✓ upload_quotas_router: {upload_quotas_router.prefix}")
    print("\n✅ All imports from app.routes successful!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
