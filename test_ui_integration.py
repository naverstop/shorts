"""
UI Integration Test - Create Sample Data
Creates sample data for testing UI functionality
"""
import requests
import json

API_BASE = "http://localhost:8001"

def login():
    login_data = "username=testadmin&password=Test123!"
    response = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response.json()["access_token"]

def create_sample_job(token, platforms):
    """Create a sample job for testing"""
    print("\n📝 Creating sample Job...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    youtube_platform = next((p for p in platforms if p['platform_code'] == 'youtube'), None)
    if not youtube_platform:
        print("❌ YouTube platform not found")
        return
    
    job_data = {
        "platform_id": youtube_platform['id'],
        "title": "UI 테스트 영상 - Dashboard 확인",
        "script": "안녕하세요! 이것은 새로운 UI를 테스트하기 위한 샘플 Job입니다.",
        "source_language": "ko",
        "target_languages": ["ko"],
        "priority": 5
    }
    
    response = requests.post(f"{API_BASE}/api/v1/jobs", json=job_data, headers=headers)
    if response.status_code == 200:
        job = response.json()
        print(f"✅ Job created: #{job['id']} - {job['title']}")
    else:
        print(f"❌ Job creation failed: {response.text}")

def create_sample_quota(token, platforms):
    """Create sample upload quota"""
    print("\n📊 Creating sample Upload Quota...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    youtube_platform = next((p for p in platforms if p['platform_code'] == 'youtube'), None)
    if not youtube_platform:
        print("❌ YouTube platform not found")
        return
    
    quota_data = {
        "platform_id": youtube_platform['id'],
        "daily_limit": 5,
        "weekly_limit": 20,
        "monthly_limit": 80
    }
    
    response = requests.post(f"{API_BASE}/api/v1/upload-quotas", json=quota_data, headers=headers)
    if response.status_code == 200:
        print(f"✅ Upload Quota created for YouTube: 5/20/80 (daily/weekly/monthly)")
    else:
        print(f"❌ Quota creation failed: {response.text}")

def collect_trends(token):
    """Trigger trend collection"""
    print("\n📈 Triggering Trend Collection...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    trend_data = {
        "region_code": "KR"
    }
    
    response = requests.post(f"{API_BASE}/api/v1/trends/collect", json=trend_data, headers=headers)
    if response.status_code == 200:
        print(f"✅ Trend collection started for region KR (background task)")
        print(f"   ⏳ Wait 30-60 seconds, then check Trends section")
    else:
        print(f"ℹ️ Trend collection: {response.text}")

def generate_script(token):
    """Generate AI script"""
    print("\n📝 Generating AI Script...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    script_data = {
        "topic": "간단한 다이어트 팁",
        "target_audience": "20-30대",
        "platform": "youtube",
        "language": "ko",
        "duration": 60
    }
    
    response = requests.post(f"{API_BASE}/api/v1/scripts", json=script_data, headers=headers)
    if response.status_code == 200:
        print(f"✅ Script generation started (background task)")
        print(f"   ⏳ Wait 30-60 seconds, then check Scripts section")
    else:
        print(f"ℹ️ Script generation: {response.text}")

def main():
    print("="*60)
    print("  🧪 UI INTEGRATION TEST - Sample Data Creation")
    print("="*60)
    
    print("\n🔐 Logging in...")
    token = login()
    print("✅ Logged in as testadmin")
    
    print("\n🌐 Fetching platforms...")
    response = requests.get(f"{API_BASE}/api/v1/platforms")
    platforms = response.json()
    print(f"✅ {len(platforms)} platforms available")
    
    # Create sample data
    create_sample_job(token, platforms)
    create_sample_quota(token, platforms)
    collect_trends(token)
    generate_script(token)
    
    print("\n" + "="*60)
    print("  ✅ SAMPLE DATA CREATION COMPLETE")
    print("="*60)
    print("""
    Created:
    ✅ 1 Sample Job (pending)
    ✅ 1 Upload Quota (YouTube)
    ⏳ Trend Collection (background, wait 30-60s)
    ⏳ Script Generation (background, wait 30-60s)
    
    Next Steps:
    1. Open http://localhost:3000
    2. Login: testadmin / Test123!
    3. Navigate to each section:
       - Home: See system health and stats
       - Agents: (empty - need Android app)
       - Jobs: See the created job
       - Platforms: See 5 platforms
       - Credentials: (empty - need OAuth setup)
       - Trends: Wait 1 min, refresh to see data
       - Scripts: Wait 1 min, refresh to see data
       - Quotas: See YouTube quota
    
    4. Test UI features:
       - Create new jobs
       - Create new quotas
       - Delete quotas
       - Collect trends
       - Generate scripts
    """)

if __name__ == "__main__":
    main()
