import requests
import json

def test_internet_search():
    url = "http://localhost/rag/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    query = "What is the latest news about Space X as of today?"
    print(f"Testing Query: {query}")
    
    data = {
        "model": "mistral",
        "messages": [{"role": "user", "content": query}],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=300)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print("\nResponse Content:")
            print("-" * 50)
            print(content)
            print("-" * 50)
            
            # Check if sources mention tool
            if "Sources:" in content or "Tool used:" in content:
                print("\n✅ Evidence of tool usage found in response.")
            else:
                print("\n⚠️ No explicit evidence of tool usage in response content, check logs.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_internet_search()
