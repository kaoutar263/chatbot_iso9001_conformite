from pydantic import BaseModel

class DocumentUploadResponse(BaseModel):
    status: str
    chunks_added: int
