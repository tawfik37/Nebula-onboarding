from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    thread_id: Optional[str] = "default_thread"

class ChatResponse(BaseModel):
    answer: str
