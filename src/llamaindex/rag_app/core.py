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
from qdrant_client import QdrantClient, AsyncQdrantClient
from minio import Minio
from .config import settings
from .models import QueryResponse, SourceNode
from .tools import search_internet
import tempfile
import re
import logging

logger = logging.getLogger(__name__)

# Keywords that indicate user wants to search the internet
INTERNET_KEYWORDS = [
    # Thai
    "ค้นหา", "หาข้อมูล", "internet", "อินเทอร์เน็ต", "เว็บ", "ออนไลน์",
    "ข่าว", "ล่าสุด", "ปัจจุบัน", "วันนี้", "ตอนนี้", "อัพเดท", "อัปเดต",
    "เมื่อวาน", "สัปดาห์นี้", "เดือนนี้", "ปีนี้",
    "ราคา", "หุ้น", "ค่าเงิน", "สภาพอากาศ", "พยากรณ์",
    "search", "google", "ค้นเว็บ", "ค้นหาในเว็บ", "ค้นหาใน internet",
    "ค้นหาข้อมูลจาก", "เสิร์ช",
    # English
    "search the internet", "search online", "look up", "find online",
    "latest", "current", "today", "now", "recent", "news",
    "what is the price", "weather", "stock", "update",
    "who won", "score", "result",
]


def should_search_internet(query: str) -> bool:
    """Determine if the query should trigger an internet search."""
    query_lower = query.lower()
    for keyword in INTERNET_KEYWORDS:
        if keyword.lower() in query_lower:
            return True
    return False


class RAGService:
    def __init__(self):
        # 1. Setup LLM
        self.llm = Ollama(
            model=settings.OLLAMA_MODEL, 
            base_url=settings.OLLAMA_BASE_URL,
            request_timeout=300.0
        )
        
        # 2. Setup Embedding Model
        from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
        self.embed_model = TextEmbeddingsInference(
            base_url=settings.EMBEDDING_URL,
            timeout=60,
            model_name="BAAI/bge-m3"
        )

        # 3. Setup Vector Store
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.aclient = AsyncQdrantClient(url=settings.QDRANT_URL)
        
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

        self.vector_store = QdrantVectorStore(
            client=self.client, 
            aclient=self.aclient, 
            collection_name=collection_name
        )
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
        if not self.minio_client.bucket_exists(settings.MINIO_BUCKET):
            self.minio_client.make_bucket(settings.MINIO_BUCKET)
        
        import io
        self.minio_client.put_object(
            settings.MINIO_BUCKET,
            filename,
            io.BytesIO(content),
            len(content)
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, filename)
            with open(temp_path, "wb") as f:
                f.write(content)
                
            reader = SimpleDirectoryReader(input_dir=temp_dir)
            documents = reader.load_data()
            
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=self.storage_context
        )
        
        return len(documents)

    async def query(self, query_text: str, top_k: int = 3) -> QueryResponse:
        use_internet = should_search_internet(query_text)
        logger.info(f"Query: '{query_text}' | Internet search: {use_internet}")
        
        if use_internet:
            # Search internet first, then ask LLM to summarize
            search_results = search_internet(query_text)
            logger.info(f"Search results length: {len(search_results)}")
            
            prompt = (
                f"Based on the following internet search results, answer the user's question.\n\n"
                f"Search Results:\n{search_results}\n\n"
                f"User Question: {query_text}\n\n"
                f"Please provide a comprehensive answer based on the search results above. "
                f"If the search results are not relevant, say so."
            )
            
            response = await self.llm.acomplete(prompt)
            return QueryResponse(
                response=str(response),
                sources=[]
            )
        else:
            # Use local RAG
            index = VectorStoreIndex.from_vector_store(self.vector_store)
            query_engine = index.as_query_engine(similarity_top_k=top_k)
            result = await query_engine.aquery(query_text)
            
            return QueryResponse(
                response=str(result.response),
                sources=[]
            )

    async def astream_query(self, query_text: str, top_k: int = 3):
        use_internet = should_search_internet(query_text)
        logger.info(f"Stream Query: '{query_text}' | Internet search: {use_internet}")
        
        if use_internet:
            search_results = search_internet(query_text)
            logger.info(f"Search results length: {len(search_results)}")
            
            prompt = (
                f"Based on the following internet search results, answer the user's question.\n\n"
                f"Search Results:\n{search_results}\n\n"
                f"User Question: {query_text}\n\n"
                f"Please provide a comprehensive answer based on the search results above. "
                f"If the search results are not relevant, say so."
            )
            
            response = await self.llm.astream_complete(prompt)
            
            async def event_gen():
                async for token in response:
                    yield token.delta
            
            return event_gen()
        else:
            # Use local RAG with streaming (fall back to non-streaming query engine)
            index = VectorStoreIndex.from_vector_store(self.vector_store)
            query_engine = index.as_query_engine(similarity_top_k=top_k, streaming=True)
            result = await query_engine.aquery(query_text)
            
            async def event_gen():
                # For streaming query engine
                if hasattr(result, 'response_gen'):
                    for token in result.response_gen:
                        yield token
                else:
                    yield str(result.response)
            
            return event_gen()

rag_service = RAGService()
