import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service URLs
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    QDRANT_URL: str = "http://qdrant:6333"
    EMBEDDING_URL: str = "http://embedding:80"
    
    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "rag-documents"
    MINIO_SECURE: bool = False

    # Keycloak
    KEYCLOAK_URL: str = "http://keycloak:8080"
    KEYCLOAK_REALM: str = "rag-realm"
    KEYCLOAK_CLIENT_ID: str = "rag-client"
    
    # App
    chunk_size: int = 512
    chunk_overlap: int = 50

settings = Settings()
