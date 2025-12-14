from pypdf import PdfReader
import io
import pandas as pd

def process_pdf_stream(file_stream) -> list[str]:
    """
    Extracts text from a PDF file stream (bytes) and chunks it.
    Returns a list of text chunks.
    """
    try:
        pdf = PdfReader(file_stream)
        chunks = []
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text and len(text) > 100:  # Ignore empty/short pages
                # Simple chunking by paragraphs for now
                paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
                chunks.extend(paragraphs)
        return chunks
    except Exception as e:
        print(f"PDF Error: {e}")
        return []

def process_file_stream(file_stream, filename: str) -> list[str]:
    """
    Generic processing dependent on file extension.
    Supports: .pdf, .md, .xlsx, .xls
    """
    filename = filename.lower()
    
    if filename.endswith(".pdf"):
        return process_pdf_stream(file_stream)
        
    elif filename.endswith(".md"):
        # Decode bytes to string
        try:
            text = file_stream.read().decode("utf-8")
            # Chunk by headers or double newlines
            chunks = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
            return chunks
        except Exception as e:
            print(f"Markdown Error: {e}")
            return []
            
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        try:
            chunks = []
            # Read all sheets
            excel_file = pd.ExcelFile(file_stream)
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                # Convert to markdown table string or text
                text_content = f"Sheet: {sheet_name}\n" + df.to_markdown(index=False)
                # If too large, we might need to split rows, but for now we treat sheet as chunk basis
                chunks.append(text_content)
            return chunks
        except Exception as e:
            print(f"Excel Error: {e}")
            return []
            
    return []
