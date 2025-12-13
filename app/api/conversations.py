from fastapi import APIRouter, UploadFile, File
from uuid import uuid4
from app.schemas.conversation import (
    ConversationCreateResponse,
    ConversationListResponse
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import DocumentUploadResponse
import chromadb
from chromadb.config import Settings
from groq import Groq
import os
import json

# Initialize Groq Client
client = Groq(
    api_key="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
)

# Initialize ChromaDB Client
chroma_client = chromadb.PersistentClient(
    path="./data/chroma_db",
    settings=Settings(anonymized_telemetry=False)
)
collection = chroma_client.get_or_create_collection("iso_docs")

def get_chroma_collection():
    return collection


router = APIRouter()

# 🟦 CONVERSATION MANAGEMENT

import sqlite3
from datetime import datetime

# Database Helper
DB_PATH = "chat.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id)
            )
        """)
        conn.commit()

# Initialize DB on module load (simple approach)
init_db()

@router.post("/", response_model=ConversationCreateResponse)
def create_conversation():
    new_id = str(uuid4())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO conversations (id, created_at) VALUES (?, ?)", 
                     (new_id, datetime.now().isoformat()))
    return {"convo_id": new_id}

@router.get("/", response_model=ConversationListResponse)
def list_conversations():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT id FROM conversations")
        ids = [row[0] for row in cursor.fetchall()]
    return {"conversations": ids}

@router.get("/{convo_id}/history")
def get_conversation_history(convo_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY id ASC", (convo_id,))
        messages = [
            {"role": row[0], "content": row[1], "timestamp": row[2]} 
            for row in cursor.fetchall()
        ]
    return {"history": messages}

# 🟧 CHAT ENDPOINT

@router.post("/{convo_id}/ask", response_model=ChatResponse)
async def ask_question(convo_id: str, payload: ChatRequest):
    question = payload.message
    
    # 1. Vector Search
    collection = get_chroma_collection()
    results = collection.query(
        query_texts=[question],
        n_results=3
    )
    
    context_text = ""
    citations = []
    
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            source = meta.get("source", "Unknown")
            # Truncate content for display
            display_content = (doc[:200] + "...") if len(doc) > 200 else doc
            
            context_text += f"\n---\nSource: {source}\nContent: {doc}\n"
            citations.append({
                "source": source,
                "doc": display_content,
                "chunk_id": results["ids"][0][i]
            })
    
    # 2. LLM Generation
    system_prompt = f"""You are an ISO 9001 compliance expert. Answer the question based ONLY on the provided context.
    
    Context:
    {context_text}
    """
    
    # Select model from payload or default
    model_name = "llama-3.3-70b-versatile"
    if payload.settings and payload.settings.model:
        model_name = payload.settings.model

    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        model=model_name,
    )
    
    answer = completion.choices[0].message.content
    
    # 3. Save History (SQLite)
    timestamp = datetime.now().isoformat()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                         (convo_id, "user", question, timestamp))
            conn.execute("INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                         (convo_id, "assistant", answer, timestamp))
    except Exception as e:
        print(f"Error saving history: {e}")

    return {
        "answer": answer,
        "citations": citations
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
