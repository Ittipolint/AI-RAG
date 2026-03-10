import os
import requests
from minio import Minio

def check_qdrant():
    print("--- Qdrant Status (from container) ---")
    # Inside docker network, qdrant is at 'qdrant:6333'
    url = "http://qdrant:6333/collections/rag_collection"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            points_count = data['result']['points_count']
            print(f"Collection 'rag_collection' exists. Points count: {points_count}")
        else:
            print(f"Error fetching collection: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")

def check_minio():
    print("\n--- MinIO Status (from container) ---")
    endpoint = "minio:9000"
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    bucket_name = "rag-bucket"
    
    try:
        m = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        if m.bucket_exists(bucket_name):
            objects = m.list_objects(bucket_name)
            names = [obj.object_name for obj in objects]
            print(f"Bucket '{bucket_name}' exists. Objects: {names}")
            
            # Check for content in the bucket
            print(f"Total objects found: {len(names)}")
        else:
            print(f"Bucket '{bucket_name}' does not exist.")
    except Exception as e:
        print(f"Error connecting to MinIO: {e}")

if __name__ == "__main__":
    check_qdrant()
    check_minio()
