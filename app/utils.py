from pypdf import PdfReader
import io

def process_pdf_stream(file_stream) -> list[str]:
    """
    Extracts text from a PDF file stream (bytes) and chunks it.
    Returns a list of text chunks.
    """
    pdf = PdfReader(file_stream)
    chunks = []
    for i, page in enumerate(pdf.pages, 1):
        text = page.extract_text()
        if text and len(text) > 100:  # Ignore empty/short pages
            # Simple chunking by paragraphs for now
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
            chunks.extend(paragraphs)
    return chunks
