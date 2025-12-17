from fastapi import APIRouter, UploadFile, File, Depends
from uuid import uuid4
from app.api.auth import get_current_user
from sqlalchemy.orm import Session
from app.database import get_db, conversations, messages
from app.schemas.conversation import (
    ConversationCreateResponse,
    ConversationListResponse
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import DocumentUploadResponse
import chromadb
from chromadb.config import Settings
from app.llm import get_llm_client
from datetime import datetime
from app.utils import process_file_stream
import os
from dotenv import load_dotenv

load_dotenv()

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

@router.post("/", response_model=ConversationCreateResponse)
def create_conversation(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    new_id = str(uuid4())
    insert_stmt = conversations.insert().values(
        id=new_id,
        user_id=current_user["id"],
        created_at=datetime.utcnow().isoformat()
    )
    db.execute(insert_stmt)
    db.commit()
    return {"convo_id": new_id}

@router.get("/", response_model=ConversationListResponse)
def list_conversations(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    query = conversations.select().with_only_columns(conversations.c.id).where(conversations.c.user_id == current_user["id"])
    result = db.execute(query).fetchall()
    ids = [row.id for row in result]
    return {"conversations": ids}

@router.get("/{convo_id}/history")
def get_conversation_history(convo_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Validate ownership
    query = conversations.select().where(
        (conversations.c.id == convo_id) & (conversations.c.user_id == current_user["id"])
    )
    if not db.execute(query).fetchone():
         return {"history": []}

    msg_query = messages.select().where(messages.c.conversation_id == convo_id).order_by(messages.c.id.asc())
    result = db.execute(msg_query).fetchall()
    
    msgs = [
        {"role": row.role, "content": row.content, "timestamp": row.timestamp} 
        for row in result
    ]
    return {"history": msgs}

# 🟧 CHAT ENDPOINT

@router.post("/{convo_id}/ask", response_model=ChatResponse)
async def ask_question(convo_id: str, payload: ChatRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Validate ownership
        query = conversations.select().where(
            (conversations.c.id == convo_id) & (conversations.c.user_id == current_user["id"])
        )
        if not db.execute(query).fetchone():
             return {"answer": "Access Denied: You do not own this conversation.", "citations": []}

        question = payload.message
        
        # 1. Vector Search (Hybrid Strategy)
        collection = get_chroma_collection()
        
        # Strategy: Query global and local separately to ensure representation from both
        # This prevents large global corpora from drowning out specific local files
        
        # A. Local Scope Query
        results_local = collection.query(
            query_texts=[question],
            n_results=5,
            where={"scope": convo_id}
        )
        
        # B. Global Scope Query
        results_global = collection.query(
            query_texts=[question],
            n_results=5,
            where={"scope": "global"}
        )
        
        # Merge Results
        context_text = ""
        citations = []
        
        # Helper to process results
        def process_results(res):
            if res["documents"] and res["documents"][0]:
                for i, doc in enumerate(res["documents"][0]):
                    meta = res["metadatas"][0][i] if res["metadatas"] else {}
                    src = meta.get("source", "Unknown")
                    doc_id = res["ids"][0][i] if res["ids"] else ""
                    
                    # Deduplication check could go here if needed, but scopes are distinct
                    
                    # Truncate content for display in citations (not in context)
                    display_content = (doc[:200] + "...") if len(doc) > 200 else doc
                    
                    nonlocal context_text
                    context_text += f"\n---\nSource: {src}\nContent: {doc}\n"
                    citations.append({
                        "source": src,
                        "doc": display_content,
                        "chunk_id": doc_id
                    })

        process_results(results_local)
        process_results(results_global)
        
        if not context_text:
             context_text = "No relevant documents found."
        
        # 2. LLM Generation
        system_prompt = f"""You are an ISO 9001 compliance expert. Answer the question based ONLY on the provided context.
        
        Context:
        {context_text}
        """
        
        # Build Message History
        # Fetch last 6 messages (3 turns)
        msg_query = messages.select().where(messages.c.conversation_id == convo_id).order_by(messages.c.id.desc()).limit(6)
        history_rows = db.execute(msg_query).fetchall()[::-1]
        
        history_messages = [{"role": row.role, "content": row.content} for row in history_rows]

        # Get Generic LLM Client
        llm_client = get_llm_client()
        
        # Generate Answer
        model_name = payload.settings.model if payload.settings and payload.settings.model else None
        answer = llm_client.generate_answer(system_prompt, history_messages, question, model=model_name)
        
        # 3. Save History
        try:
            timestamp = datetime.utcnow().isoformat()
            db.execute(messages.insert().values(
                conversation_id=convo_id, role="user", content=question, timestamp=timestamp
            ))
            db.execute(messages.insert().values(
                conversation_id=convo_id, role="assistant", content=answer, timestamp=timestamp
            ))
            db.commit()
        except Exception as e:
            print(f"Error saving history: {e}")

        return {
            "answer": answer,
            "citations": citations
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "answer": f"Error: {str(e)}",
            "citations": []
        }

# 🟩 DOCUMENT MANAGEMENT

@router.post("/{convo_id}/documents", response_model=DocumentUploadResponse)
def upload_document(convo_id: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Validate ownership
    query = conversations.select().where(
        (conversations.c.id == convo_id) & (conversations.c.user_id == current_user["id"])
    )
    if not db.execute(query).fetchone():
         return {"status": "error", "chunks_added": 0}

    # 1. Process File (PDF/Excel/MD)
    try:
        # Read file into memory
        chunks = process_file_stream(file.file, file.filename)
        
        # 2. Add to ChromaDB with Scope (Upsert)
        collection = get_chroma_collection()
        ids = []
        from app.utils import generate_chunk_id
        
        for i, chunk in enumerate(chunks):
            # OLD: chunk_id = f"{convo_id}_{file.filename}_{i}"
            chunk_id = generate_chunk_id(convo_id, file.filename, i)
            ids.append(chunk_id)
            
        collection.upsert(
            documents=chunks,
            metadatas=[{
                "source": file.filename, 
                "page": "auto",
                "scope": convo_id
            } for _ in chunks],
            ids=ids
        )
        
        return {
            "status": "ok",
            "chunks_added": len(chunks)
        }
    except Exception as e:
        print(f"Upload failed: {e}")
        return {
            "status": "error",
            "chunks_added": 0
        }

@router.get("/{convo_id}/documents")
def list_documents(convo_id: str, current_user: dict = Depends(get_current_user)):
    # This is tricky with Chroma, we need to query by metadata
    # Implementing simple count for now
    collection = get_chroma_collection()
    result = collection.get(where={"scope": convo_id})
    # Extract unique sources
    sources = set()
    if result["metadatas"]:
        for m in result["metadatas"]:
            if "source" in m:
                sources.add(m["source"])
    
    return {"documents": list(sources)}

@router.delete("/{convo_id}/documents/{doc_id}")
def delete_document(convo_id: str, doc_id: str, current_user: dict = Depends(get_current_user)):
    return {"status": "deleted"}

@router.post("/documents/global", response_model=DocumentUploadResponse)
def upload_global_document(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Upload a document to the Global Knowledge Base.
    Accessible to ALL users and conversations.
    """
    try:
        # 1. Process File
        chunks = process_file_stream(file.file, file.filename)
        
        # 2. Add to ChromaDB with Scope="global" (Upsert)
        collection = get_chroma_collection()
        ids = []
        from app.utils import generate_chunk_id
        
        for i, chunk in enumerate(chunks):
            chunk_id = generate_chunk_id("global", file.filename, i)
            ids.append(chunk_id)
            
        collection.upsert(
            documents=chunks,
            metadatas=[{
                "source": file.filename, 
                "page": "auto",
                "scope": "global"
            } for _ in chunks],
            ids=ids
        )
        
        return {
            "status": "ok",
            "chunks_added": len(chunks)
        }
    except Exception as e:
        print(f"Global upload failed: {e}")
        return {
            "status": "error",
            "chunks_added": 0
        }
