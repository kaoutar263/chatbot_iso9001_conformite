from fastapi import FastAPI
from app.api.conversations import router as conversations_router

app = FastAPI(
    title="ISO 9001 AI Chatbot",
    version="1.0.0",
    description="Conversation-based RAG API for ISO 9001 compliance"
)

app.include_router(
    conversations_router,
    prefix="/api/v1/conversations",
    tags=["Conversations"]
)

@app.get("/")
def health_check():
    return {"status": "API is running"}
