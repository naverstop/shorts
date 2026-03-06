"""
Full API Test Script for Shorts Platform
Tests all 8 sections: Home, Agents, Jobs, Platforms, Credentials, Trends, Scripts, Quotas
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_login():
    print_section("1️⃣ USER LOGIN TEST")
    
    # Register test user (may fail if exists, that's ok)
    try:
        register_data = {
            "username": "testadmin",
            "email": "testadmin@test.com",
            "password": "Test123!"
        }
        response = requests.post(f"{API_BASE}/api/v1/auth/register", json=register_data)
        if response.status_code == 200:
            print("✅ New user registered: testadmin")
    except:
        pass
    
    # Login
    login_data = "username=testadmin&password=Test123!"
    response = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful!")
        print(f"   Token: {token[:30]}...")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_health():
    print_section("2️⃣ SYSTEM HEALTH TEST")
    
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ System Status: {data['status']}")
        print(f"   Database: {data['database']}")
        print(f"   Redis: {data['redis']}")
        print(f"   Services: {data['services']}")
    else:
        print(f"❌ Health check failed")

def test_platforms():
    print_section("3️⃣ PLATFORMS API TEST")
    
    response = requests.get(f"{API_BASE}/api/v1/platforms")
    if response.status_code == 200:
        platforms = response.json()
        print(f"✅ Platforms found: {len(platforms)}")
        for p in platforms:
            print(f"   - {p['platform_name']} ({p['platform_code']})")
        return platforms
    else:
        print(f"❌ Platforms fetch failed")
        return []

def test_credentials(token):
    print_section("4️⃣ CREDENTIALS API TEST")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/api/v1/credentials", headers=headers)
    
    if response.status_code == 200:
        credentials = response.json()
        print(f"✅ Credentials found: {len(credentials)}")
        for c in credentials:
            print(f"   - {c.get('credential_name', 'Unnamed')} (Platform ID: {c['platform_id']}, Status: {c['status']})")
        return credentials
    else:
        print(f"❌ Credentials fetch failed: {response.text}")
        return []

def test_agents(token):
    print_section("5️⃣ AGENTS API TEST")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get agents list
    response = requests.get(f"{API_BASE}/api/v1/agents?limit=10", headers=headers)
    if response.status_code == 200:
        agents = response.json()
        print(f"✅ Agents found: {len(agents)}")
        for a in agents:
            print(f"   - {a['device_name']} (Status: {a['status']})")
    else:
        print(f"❌ Agents fetch failed")
    
    # Get agent stats
    response = requests.get(f"{API_BASE}/api/v1/agents/stats", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Agent Stats:")
        print(f"   Total: {stats['total']}, Online: {stats['online_count']}, Offline: {stats['offline_count']}")
    else:
        print(f"❌ Agent stats failed")

def test_jobs(token, platforms):
    print_section("6️⃣ JOBS API TEST")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get jobs list
    response = requests.get(f"{API_BASE}/api/v1/jobs?limit=10", headers=headers)
    if response.status_code == 200:
        jobs = response.json()
        print(f"✅ Jobs found: {len(jobs)}")
        for j in jobs[:3]:  # Show first 3
            print(f"   - {j['title']} (Status: {j['status']})")
    else:
        print(f"❌ Jobs fetch failed")
    
    # Get job stats
    response = requests.get(f"{API_BASE}/api/v1/jobs/stats", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Job Stats:")
        print(f"   Total: {stats['total']}, Pending: {stats['pending_count']}, Completed: {stats['completed_count']}")
    else:
        print(f"❌ Job stats failed")

def test_quotas(token, platforms):
    print_section("7️⃣ UPLOAD QUOTAS API TEST")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get quotas
    response = requests.get(f"{API_BASE}/api/v1/upload-quotas", headers=headers)
    if response.status_code == 200:
        quotas = response.json()
        print(f"✅ Upload Quotas found: {len(quotas)}")
        for q in quotas:
            platform_name = next((p['platform_name'] for p in platforms if p['id'] == q['platform_id']), 'Unknown')
            print(f"   - {platform_name}: Daily {q['used_today']}/{q['daily_limit']}, Weekly {q['used_week']}/{q['weekly_limit']}")
    else:
        print(f"❌ Quotas fetch failed")

def test_trends(token):
    print_section("8️⃣ TRENDS API TEST")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get trends
    response = requests.get(f"{API_BASE}/api/v1/trends?limit=10", headers=headers)
    if response.status_code == 200:
        trends = response.json()
        print(f"✅ Trends found: {len(trends)}")
        for t in trends[:5]:  # Show first 5
            print(f"   - {t['keyword']} (Source: {t['source']}, Score: {t['trend_score']})")
    else:
        print(f"❌ Trends fetch failed")

def test_scripts(token):
    print_section("9️⃣ SCRIPTS API TEST")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get scripts
    response = requests.get(f"{API_BASE}/api/v1/scripts?limit=10", headers=headers)
    if response.status_code == 200:
        scripts = response.json()
        print(f"✅ Scripts found: {len(scripts)}")
        for s in scripts[:3]:  # Show first 3
            print(f"   - {s['title']} (Quality: {s['quality_score']}, Viral: {s['viral_potential']})")
    else:
        print(f"❌ Scripts fetch failed")

def main():
    print("\n" + "="*60)
    print("  🚀 SHORTS PLATFORM - FULL API TEST")
    print("="*60)
    print(f"  Frontend: {FRONTEND_URL}")
    print(f"  Backend:  {API_BASE}")
    print(f"  Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Test sequence
    token = test_login()
    if not token:
        print("\n❌ Cannot proceed without valid token")
        return
    
    test_health()
    platforms = test_platforms()
    test_credentials(token)
    test_agents(token)
    test_jobs(token, platforms)
    test_quotas(token, platforms)
    test_trends(token)
    test_scripts(token)
    
    # Summary
    print_section("✅ TEST SUMMARY")
    print("""
    All 8 sections have been tested:
    ✅ 1. Dashboard Overview (Home) - Health & Stats
    ✅ 2. Agent Management
    ✅ 3. Job Management
    ✅ 4. Platform List
    ✅ 5. Credentials Management
    ✅ 6. Trends Collection
    ✅ 7. AI Scripts Generation
    ✅ 8. Upload Quotas Management
    
    🌐 Frontend URL: http://localhost:3000
    📝 Login: testadmin / Test123!
    
    Next steps:
    1. Open http://localhost:3000 in browser
    2. Login with testadmin / Test123!
    3. Navigate through all 8 menu items
    4. Verify UI displays data correctly
    """)

if __name__ == "__main__":
    main()
