from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api import conversations, auth
from app.database import init_db

app = FastAPI(title="ISO 9001 RAG Chatbot")

# Initialize DB
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])

@app.get("/")
def health_check():
    return {"status": "API is running"}
