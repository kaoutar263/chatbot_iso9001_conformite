import chromadb
from chromadb.config import Settings
from pypdf import PdfReader  # <-- CHANGÉ ICI : pypdf au lieu de PyPDF2
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IngestionISO:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./data/chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection("iso_docs")
    
    def process_pdf(self, pdf_path: str):
        """Extrait et découpe un PDF ISO"""
        with open(pdf_path, 'rb') as f:
            pdf = PdfReader(f)  # <-- CHANGÉ ICI : PdfReader de pypdf
            chunks = []
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if len(text) > 100:  # Ignore pages vides
                    # Découpage simple par paragraphes
                    paragraphs = [p for p in text.split('\n\n') if len(p) > 50]
                    chunks.extend(paragraphs)
        return chunks
    
    def run(self):
        """Pipeline complet d'ingestion"""
        logger.info("📚 Ingestion des documents ISO...")
        
        for pdf_file in Path("app/documents").glob("*.pdf"):
            logger.info(f"  Processing: {pdf_file.name}")
            chunks = self.process_pdf(str(pdf_file))
            
            # Ajout à Chromadb
            for i, chunk in enumerate(chunks):
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{"source": pdf_file.name, "page": "auto"}],
                    ids=[f"{pdf_file.stem}_{i}"]
                )
            
            logger.info(f"    ✅ {len(chunks)} chunks ajoutés")
        
        logger.info(f"🎯 Base prête: {self.collection.count()} documents")

if __name__ == "__main__":
    IngestionISO().run()