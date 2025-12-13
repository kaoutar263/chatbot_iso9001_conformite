from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel  # <-- IMPORT AJOUTÉ
import chromadb
from chromadb.config import Settings
import redis
import json
from datetime import datetime

app = FastAPI(title="Chatbot ISO Compliance")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèle Pydantic pour la requête
class QuestionRequest(BaseModel):
    question: str
    session_id: str = "default"

# Redis client (toujours présent)
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

# Fonction pour obtenir la collection ChromaDB
def get_chroma_collection():
    """Retourne la collection ChromaDB, la crée si nécessaire"""
    client = chromadb.PersistentClient(
        path="./data/chroma_db",
        settings=Settings(anonymized_telemetry=False)
    )
    try:
        return client.get_collection("iso_docs")
    except Exception:
        # Collection n'existe pas encore
        return client.get_or_create_collection("iso_docs")

@app.get("/")
def root():
    return {"message": "Chatbot ISO - API opérationnelle"}

@app.get("/health")
def health():
    """Endpoint de santé - NE PAS appeler get_chroma_collection() ici"""
    try:
        # Test simple sans charger la collection
        client = chromadb.PersistentClient(
            path="./data/chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        collections = client.list_collections()
        chroma_ok = any(c.name == "iso_docs" for c in collections)
    except Exception:
        chroma_ok = False
    
    return {
        "api": "healthy",
        "chromadb": chroma_ok,
        "redis": redis_client.ping()
    }

@app.post("/api/v1/ask")
def ask_question(request: QuestionRequest):  # <-- MODIFIÉ ICI
    """
    Endpoint principal : question → réponse avec citations ISO
    Accepte maintenant JSON dans le body
    """
    question = request.question
    session_id = request.session_id
    
    # 1. Obtenir la collection (crée si nécessaire)
    collection = get_chroma_collection()
    
    # 2. Recherche dans Chromadb
    results = collection.query(
        query_texts=[question],
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )
    
    # 3. Sauvegarde historique (Redis)
    history_key = f"session:{session_id}"
    redis_client.rpush(history_key, json.dumps({
        "question": question,
        "timestamp": datetime.now().isoformat(),  # <-- TIMESTAMP RÉEL
        "sources": results["metadatas"][0] if results["metadatas"] else []
    }))
    
    # 4. Construction réponse
    if results["documents"] and results["documents"][0]:
        answer = {
            "question": question,
            "answer": f"Trouvé {len(results['documents'][0])} références pertinentes.",
            "sources": results["metadatas"][0] if results["metadatas"] else [],
            "citations": results["documents"][0][:2]  # 2 premières citations
        }
    else:
        answer = {
            "question": question,
            "answer": "Aucune référence trouvée dans la base ISO.",
            "sources": [],
            "citations": []
        }
    
    return answer

@app.get("/api/v1/history/{session_id}")
def get_history(session_id: str, limit: int = 10):
    """Récupère l'historique d'une session"""
    history_key = f"session:{session_id}"
    items = redis_client.lrange(history_key, 0, limit-1)
    return {"session": session_id, "history": [json.loads(item) for item in items]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)