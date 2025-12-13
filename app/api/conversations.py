from fastapi import APIRouter, UploadFile, File
from uuid import uuid4
from app.schemas.conversation import (
    ConversationCreateResponse,
    ConversationListResponse
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import DocumentUploadResponse

router = APIRouter()

# 🟦 CONVERSATION MANAGEMENT

@router.post("/", response_model=ConversationCreateResponse)
def create_conversation():
    return {"convo_id": str(uuid4())}

@router.get("/", response_model=ConversationListResponse)
def list_conversations():
    return {"conversations": ["uuid-1", "uuid-2"]}

@router.get("/{convo_id}/history")
def get_conversation_history(convo_id: str):
    return {"history": []}  # Redis later

# 🟧 CHAT ENDPOINT

@router.post("/{convo_id}/ask", response_model=ChatResponse)
def ask_question(convo_id: str, payload: ChatRequest):
    return {
        "answer": "Mock answer. RAG pipeline not implemented yet.",
        "citations": []
    }

# 🟩 DOCUMENT MANAGEMENT

@router.post("/{convo_id}/documents", response_model=DocumentUploadResponse)
def upload_document(convo_id: str, file: UploadFile = File(...)):
    return {
        "status": "ok",
        "chunks_added": 0
    }

@router.get("/{convo_id}/documents")
def list_documents(convo_id: str):
    return {"documents": []}

@router.delete("/{convo_id}/documents/{doc_id}")
def delete_document(convo_id: str, doc_id: str):
    return {"status": "deleted"}
