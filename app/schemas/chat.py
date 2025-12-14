from pydantic import BaseModel
from typing import Optional, List

class ChatSettings(BaseModel):
    model: Optional[str] = "llama-3.3-70b-versatile"
    temperature: Optional[float] = 0.2

class ChatRequest(BaseModel):
    message: str
    settings: Optional[ChatSettings] = None

class Citation(BaseModel):
    source: str
    doc: str
    chunk_id: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
