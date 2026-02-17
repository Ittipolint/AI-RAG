import requests
import json
import os

# Configuration
KEYCLOAK_URL = "http://localhost/auth"
API_URL = "http://localhost/api"
REALM = "rag-realm"
CLIENT_ID = "rag-client"
USERNAME = "user"
PASSWORD = "password"

def get_token():
    url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    payload = {
        "client_id": CLIENT_ID,
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password"
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get token: {response.text}")
        return None

def test_ingest(token, filename, content):
    url = f"{API_URL}/ingest"
    headers = {"Authorization": f"Bearer {token}"}
    files = {'file': (filename, content)}
    response = requests.post(url, headers=headers, files=files)
    print(f"Ingest Status: {response.status_code}")
    print(f"Ingest Response: {response.json()}")
    return response.status_code == 200

def test_query(token, query):
    url = f"{API_URL}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "similarity_top_k": 3
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Query Status: {response.status_code}")
    print(f"Query Response: {response.json()}")
    return response.status_code == 200

if __name__ == "__main__":
    print("--- Starting Validation ---")
    
    # 1. Get Token
    token = get_token()
    if not token:
        exit(1)
    print("Authentication successful.")

    # 2. Ingest
    test_content = b"The capital of France is Paris. The capital of Germany is Berlin."
    if test_ingest(token, "cities.txt", test_content):
        print("Ingestion successful.")
    else:
        print("Ingestion failed.")
        exit(1)

    # 3. Query
    if test_query(token, "What is the capital of France?"):
        print("Query successful.")
    else:
        print("Query failed.")
        exit(1)
        
    print("--- Validation Complete ---")
