from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
import json
import time
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
    ModelList,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    DeltaMessage
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
        result = await rag_service.query(request.query, request.similarity_top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/v1/models", response_model=ModelList)
async def list_models():
    # Give it a unique, obvious name so the user selects this API instead of raw Ollama
    models = [
        Model(id="🌐 RAG + Internet Search (Qwen 2.5)"),
    ]
    return ModelList(data=models)

@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest
):
    try:
        # 1. Extract the last user message
        last_message = next((m for m in reversed(request.messages) if m.role == "user"), None)
        if not last_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        query_text = last_message.content

        # 2. Handle Streaming
        if request.stream:
            async def stream_generator():
                try:
                    response_gen = await rag_service.astream_query(query_text, top_k=3)
                    chunk_id = f"chatcmpl-{int(time.time())}"
                    
                    # Yield role first
                    start_chunk = ChatCompletionChunk(
                        id=chunk_id, 
                        model=request.model, 
                        choices=[ChatCompletionChunkChoice(index=0, delta=DeltaMessage(role='assistant'), finish_reason=None)]
                    )
                    yield f"data: {start_chunk.model_dump_json()}\n\n"

                    # Iterating over async generator
                    async for text in response_gen:
                        if not text:
                            continue
                        chunk = ChatCompletionChunk(
                            id=chunk_id,
                            model=request.model,
                            choices=[ChatCompletionChunkChoice(index=0, delta=DeltaMessage(content=str(text)), finish_reason=None)]
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"
                    
                    end_chunk = ChatCompletionChunk(
                        id=chunk_id, 
                        model=request.model, 
                        choices=[ChatCompletionChunkChoice(index=0, delta=DeltaMessage(), finish_reason='stop')]
                    )
                    yield f"data: {end_chunk.model_dump_json()}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    print(f"STREAMING ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    yield "data: [DONE]\n\n"

            return StreamingResponse(stream_generator(), media_type="text/event-stream")

        # 3. Handle Non-Streaming
        result = await rag_service.query(query_text, top_k=3)
        final_response_text = result.response
        if result.sources:
            final_response_text += "\n\n**Sources:**\n"
            for i, source in enumerate(result.sources, 1):
                snippet = source.text[:200] + "..." if len(source.text) > 200 else source.text
                final_response_text += f"{i}. {snippet}\n"

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
            usage=Usage()
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
