import requests
import json

BASE_URL = "http://localhost/rag"

def test_models():
    print("=== Test /v1/models ===")
    try:
        r = requests.get(f"{BASE_URL}/v1/models", timeout=10)
        if r.status_code == 200:
            print(f"Models: {json.dumps(r.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_models()
