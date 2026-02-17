import requests
import json
import time
import sys

def check_health():
    try:
        print("Checking API health...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Health check passed")
            return True
        else:
            print(f"❌ API Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health check failed: {str(e)}")
        return False

def check_chat_completion():
    print("Checking Chat Completion API...")
    url = "http://localhost:8000/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "mistral",
        "messages": [{"role": "user", "content": "Hello, are you working?"}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print("✅ Chat Completion passed")
            print(f"   Response: {content[:100]}...")
            return True
        else:
            print(f"❌ Chat Completion failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat Completion check failed: {str(e)}")
        return False

def main():
    print("Waiting for services to settle (10s)...")
    time.sleep(10)
    
    health_ok = check_health()
    if not health_ok:
        sys.exit(1)
        
    chat_ok = check_chat_completion()
    if not chat_ok:
        sys.exit(1)
        
    print("\n🎉 System Verification Successful!")

if __name__ == "__main__":
    main()
