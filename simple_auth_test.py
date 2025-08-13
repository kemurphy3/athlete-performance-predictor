# Create simple_auth_test.py
import requests

def test_auth():
    base_url = "http://localhost:8000"
    
    print("🔍 Testing authentication step by step...")
    
    # 1. Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health: {response.status_code}")
    except Exception as e:
        print(f"❌ Health error: {e}")
        return
    
    # 2. Login to get token
    try:
        login_data = {
            "email": "kemurphy3@gmail.com",
            "password": "testpassword123"
        }
        
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"Login: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"✅ Token obtained: {token[:30]}...")
            
            # 3. Test protected endpoint
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{base_url}/api/workouts", headers=headers)
            print(f"Workouts: {response.status_code} - {response.text}")
            
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_auth()