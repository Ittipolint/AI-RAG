import os
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    SimpleDirectoryReader,
    Settings as LlamaSettings,
    Document
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from minio import Minio
from .config import settings
from .models import QueryResponse, SourceNode
import tempfile

class RAGService:
    def __init__(self):
        # 1. Setup LLM
        self.llm = Ollama(
            model="mistral", 
            base_url=settings.OLLAMA_BASE_URL,
            request_timeout=300.0
        )
        
        # 2. Setup Embedding Model (Remote execution via TEI or local fallback?)
        # The requirement asks to use "bge-m3 (HuggingFace inference container)"
        # LlamaIndex doesn't have a direct "TEI" embedding class out of the box in strict sense 
        # unless we use TextEmbeddingsInference class usually found in langchain or community extras.
        # But we can use the OpenAIDeli class pointing to TEI if it mimics OpenAI, OR
        # better yet, since we are in python, we can just use HuggingFaceEmbedding locally if the weight is small
        # BUT the requirement says "bge-m3 container".
        # So we should use the `TextEmbeddingsInference` class if available or a generic client.
        
        # Checking available classes... TextEmbeddingsInference is the standard way to talk to TEI.
        # If not available in this version, we might have to write a custom wrapper or use OpenAILike.
        # TEI mimics the extensive HF API.
        
        # Let's try to use the specific TextEmbeddingsInference class if we can find it, 
        # or use generic OpenAIBase if TEI provides an OpenAI compatible endpoint (it does /v1/embeddings).
        
        # For simplicity and robustness with the requested specific container architecture (TEI):
        # TEI exposes /embed.
        
        from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
        self.embed_model = TextEmbeddingsInference(
            base_url=settings.EMBEDDING_URL,
            timeout=60,
            model_name="BAAI/bge-m3" # This is just a label here usually
        )

        
        # 3. Setup Vector Store
        self.client = QdrantClient(url=settings.QDRANT_URL)
        
        # Ensure collection exists
        collection_name = "rag_collection"
        if not self.client.collection_exists(collection_name):
            from qdrant_client.http import models as qmodels
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=qmodels.VectorParams(
                    size=1024, # bge-m3 dimension
                    distance=qmodels.Distance.COSINE
                )
            )

        self.vector_store = QdrantVectorStore(client=self.client, collection_name=collection_name)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        # 4. Setup Global Settings
        LlamaSettings.llm = self.llm
        LlamaSettings.embed_model = self.embed_model
        LlamaSettings.chunk_size = settings.chunk_size
        LlamaSettings.chunk_overlap = settings.chunk_overlap

        # 5. Setup MinIO Client
        self.minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

    def ingest_document(self, filename: str, content: bytes) -> int:
        # Save to MinIO
        if not self.minio_client.bucket_exists(settings.MINIO_BUCKET):
            self.minio_client.make_bucket(settings.MINIO_BUCKET)
        
        # Put object
        import io
        self.minio_client.put_object(
            settings.MINIO_BUCKET,
            filename,
            io.BytesIO(content),
            len(content)
        )

        # Create Document
        # Depending on file type, we might need specific parsing. 
        # For simplicity, we'll try to treat it as text if possible or use SimpleDirectoryReader
        # by saving to a temp file.
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, filename)
            with open(temp_path, "wb") as f:
                f.write(content)
                
            reader = SimpleDirectoryReader(input_dir=temp_dir)
            documents = reader.load_data()
            
        # Index
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=self.storage_context
        )
        
        return len(documents)

    def query(self, query_text: str, top_k: int = 3) -> QueryResponse:
        # Reload index from vector store
        index = VectorStoreIndex.from_vector_store(
            self.vector_store,
        )
        
        query_engine = index.as_query_engine(similarity_top_k=top_k)
        response = query_engine.query(query_text)
        
        return QueryResponse(
            response=str(response),
            sources=[
                SourceNode(
                    text=node.node.get_content(),
                    score=node.score,
                    metadata=node.node.metadata
                )
                for node in response.source_nodes
            ]
        )

rag_service = RAGService()
