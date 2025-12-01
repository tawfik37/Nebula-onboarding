from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    query: str
    thread_id: Optional[str] = "default_thread"  # For remembering conversation history later

class ChatResponse(BaseModel):
    answer: str