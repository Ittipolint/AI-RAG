from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import Annotated, List
from .models import (
    IngestResponse, 
    QueryRequest, 
    QueryResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    Message,
    Usage,
    Model,
    ModelList
)
from .core import rag_service
from .auth import get_current_user

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "RAG Service API is running", "endpoints": ["/health", "/ingest", "/query", "/v1/chat/completions"]}

@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        content = await file.read()
        num_docs = rag_service.ingest_document(file.filename, content)
        return IngestResponse(
            filename=file.filename,
            status="success",
            chunks_created=num_docs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = rag_service.query(request.query, request.similarity_top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/v1/models", response_model=ModelList)
async def list_models():
    return ModelList(data=[Model(id="mistral")])

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest
):
    try:
        # 1. Extract the last user message
        last_message = next((m for m in reversed(request.messages) if m.role == "user"), None)
        if not last_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        query_text = last_message.content

        # 2. Query RAG Service
        # We use a default top_k or could infer from request if needed
        result = rag_service.query(query_text, top_k=3)

        # 3. Format Response
        # Append sources to the response text for visibility in WebUI
        final_response_text = result.response
        if result.sources:
            final_response_text += "\n\n**Sources:**\n"
            for i, source in enumerate(result.sources, 1):
                # Truncate source text if too long
                snippet = source.text[:200] + "..." if len(source.text) > 200 else source.text
                final_response_text += f"{i}. {snippet}\n"

        # 4. Construct OpenAI-compatible response
        return ChatCompletionResponse(
            model=request.model,
            choices=[
                Choice(
                    index=0,
                    message=Message(
                        role="assistant",
                        content=final_response_text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=Usage() # We don't track tokens yet
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
