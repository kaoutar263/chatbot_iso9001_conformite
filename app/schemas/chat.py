from pydantic import BaseModel
from typing import Optional, List

class ChatSettings(BaseModel):
    model: Optional[str] = "gemini-pro"
    temperature: Optional[float] = 0.2

class ChatRequest(BaseModel):
    message: str
    settings: Optional[ChatSettings]

class Citation(BaseModel):
    source: str
    doc: str
    chunk_id: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
