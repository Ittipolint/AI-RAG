import requests
import json

def test_api():
    url = "http://localhost/rag/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    # Test Non-Streaming
    print("Testing Non-Streaming...")
    data = {
        "model": "mistral",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": False
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Test Streaming
    print("\nTesting Streaming...")
    data["stream"] = True
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30, stream=True)
        print(f"Status: {response.status_code}")
        for line in response.iter_lines():
            if line:
                print(f"Chunk: {line.decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
