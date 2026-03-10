import os
import requests
from minio import Minio
from dotenv import load_dotenv

load_dotenv()

def check_qdrant():
    print("--- Qdrant Status ---")
    url = "http://localhost:6333/collections/rag_collection"
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
    print("\n--- MinIO Status ---")
    endpoint = "localhost:9000"
    access_key = os.getenv("MINIO_ROOT_USER")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD")
    bucket_name = "rag-bucket"
    
    try:
        m = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        if m.bucket_exists(bucket_name):
            objects = m.list_objects(bucket_name)
            names = [obj.object_name for obj in objects]
            print(f"Bucket '{bucket_name}' exists. Objects: {names}")
        else:
            print(f"Bucket '{bucket_name}' does not exist.")
    except Exception as e:
        print(f"Error connecting to MinIO: {e}")

if __name__ == "__main__":
    check_qdrant()
    check_minio()
