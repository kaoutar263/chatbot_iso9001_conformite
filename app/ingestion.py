import chromadb
from chromadb.config import Settings
from pathlib import Path
import logging
from app.utils import process_pdf_stream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IngestionISO:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./data/chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection("iso_docs")
    
    def run(self):
        """Pipeline complet d'ingestion"""
        logger.info("📚 Ingestion des documents ISO...")
        
        for pdf_file in Path("app/documents").glob("*.pdf"):
            logger.info(f"  Processing: {pdf_file.name}")
            
            with open(pdf_file, 'rb') as f:
                chunks = process_pdf_stream(f)
            
            # Ajout à Chromadb
            for i, chunk in enumerate(chunks):
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{
                        "source": pdf_file.name, 
                        "page": "auto",
                        "scope": "global"  # <-- Added Scope
                    }],
                    ids=[f"{pdf_file.stem}_{i}"]
                )
            
            logger.info(f"    ✅ {len(chunks)} chunks ajoutés")
        
        logger.info(f"🎯 Base prête: {self.collection.count()} documents")

if __name__ == "__main__":
    IngestionISO().run()