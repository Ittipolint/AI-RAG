import requests
import json

# Direct to LlamaIndex through nginx /rag/ prefix
BASE_URL = "http://localhost/rag"

def test_health():
    print("=== Test Health ===")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status: {r.status_code}, Body: {r.json()}")
    except Exception as e:
        print(f"Error: {e}")

def test_models():
    print("\n=== Test /v1/models ===")
    try:
        r = requests.get(f"{BASE_URL}/v1/models", timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Models: {json.dumps(r.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_internet_search():
    print("\n=== Test Internet Search ===")
    payload = {
        "model": "qwen2.5:1.5b",
        "messages": [
            {"role": "user", "content": "ค้นหาข่าวล่าสุดเกี่ยวกับ AI"}
        ],
        "stream": False
    }
    try:
        r = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, timeout=120)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            print(f"Response:\n{content[:800]}")
        else:
            print(f"Error: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_health()
    test_models()
    test_internet_search()
