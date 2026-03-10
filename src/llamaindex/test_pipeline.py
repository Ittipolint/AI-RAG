import sys
import os
# Add current directory to path so it can find rag_app
sys.path.append(os.getcwd())

from rag_app.core import rag_service

def test_pipeline():
    # Update RAGService to use tinyllama for this test
    rag_service.llm.model = "tinyllama"
    
    print("--- Testing Ingestion ---")
    filename = "test_doc.txt"
    content = b"The capital of Thailand is Bangkok. It is known for its vibrant street life and cultural landmarks."
    
    try:
        num_docs = rag_service.ingest_document(filename, content)
        print(f"Successfully ingested {num_docs} documents from {filename}")
        
        print("\n--- Testing Query ---")
        query = "What is the capital of Thailand?"
        result = rag_service.query(query)
        print(f"Query: {query}")
        print(f"Response: {result.response}")
        print(f"Sources: {len(result.sources)}")
        for i, source in enumerate(result.sources):
            print(f"Source {i+1}: {source.text[:50]}...")
            
    except Exception as e:
        print(f"Pipeline Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
