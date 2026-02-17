from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union
import time

# --- Existing Models ---
class IngestResponse(BaseModel):
    filename: str
    status: str
    chunks_created: int

class QueryRequest(BaseModel):
    query: str
    similarity_top_k: int = 3

class SourceNode(BaseModel):
    text: str
    score: float
    metadata: dict

class QueryResponse(BaseModel):
    response: str
    sources: List[SourceNode]

# --- OpenAI Compatible Models ---

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str = "mistral" # Default, but client usually sends this
    messages: List[Message]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[dict] = None
    user: Optional[str] = None

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = "stop"

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{int(time.time())}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Usage

class Model(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "llamaindex"

class ModelList(BaseModel):
    object: str = "list"
    data: List[Model]
