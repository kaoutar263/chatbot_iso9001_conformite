import chromadb
from chromadb.config import Settings
from pathlib import Path
import logging
import io
from app.utils import process_file_stream

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
        
        # Extensions supported
        extensions = ["*.pdf", "*.md", "*.xlsx", "*.xls"]
        files = []
        for ext in extensions:
            files.extend(list(Path("app/documents").glob(ext)))
            
        for file_path in files:
            logger.info(f"  Processing: {file_path.name}")
            
            with open(file_path, 'rb') as f:
                # Load whole file into bytes for processing
                file_bytes = io.BytesIO(f.read())
                chunks = process_file_stream(file_bytes, file_path.name)
            
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