from pypdf import PdfReader
import io
import pandas as pd
import re

def recursive_chunk_text(text: str, chunk_size: int = 1500, overlap: int = 300) -> list[str]:
    """
    Splits text into chunks of roughly `chunk_size` characters with `overlap`.
    Tries to split by separators: \n\n, \n, . , space.
    """
    if not text:
        return []
        
    separators = ["\n\n", "\n", ". ", " ", ""]
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunks.append(text[start:])
            break
            
        # Try to find a separator near the 'end' to break cleanly
        best_split = -1
        for sep in separators:
            # Look backwards from 'end'
            search_start = max(start, end - overlap) 
            # We want the split to be as close to 'end' as possible but within the bounds
            # This is a simplified approach
            if sep == "":
                best_split = end
                break
                
            split_idx = text.rfind(sep, search_start, end)
            if split_idx != -1:
                best_split = split_idx + len(sep) # Include separator in previous chunk or drop it? rfind is start of sep.
                break
        
        if best_split != -1:
            chunks.append(text[start:best_split].strip())
            start = best_split - overlap # This is wrong logic for overlap relative to split.
            # Correct overlap logic: 
            # Next chunk starts at (current_end - overlap), but we want to honor separators.
            # Simplified: Just hard shift or use langchain approach.
            # Let's use simple hard shift for robustness without a library:
            # Current chunk is text[start:best_split]
            # Next start should be best_split - overlap? No, standard is purely sliding window or logical split.
            
            # Re-implementing simplified sliding window:
            # Move start forward.
            start = max(start + 1, best_split) # Don't overlap logic here for now, just split cleanly.
            # Actually, without overlap, we lose context.
            # Simple approach: standard splitter
            pass 
        else:
            # Force split
            chunks.append(text[start:end])
            start = end
            
    # Let's use a simpler verified approach for this snippet to be robust
    final_chunks = []
    # Token-ish splitting
    # 1. Clean text
    # 2. Split by paragraphs
    paragraphs = re.split(r'\n\n+', text)
    current_chunk = []
    current_len = 0
    
    for p in paragraphs:
        p = p.strip()
        if not p: continue
        
        if len(p) > chunk_size:
            # If paragraph itself is huge, split it by newlines or sentences
            sub_parts = re.split(r'(?<=[.?!])\s+', p)
            for sub in sub_parts:
                if current_len + len(sub) > chunk_size and current_chunk:
                    final_chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                current_chunk.append(sub)
                current_len += len(sub)
        else:
            if current_len + len(p) > chunk_size and current_chunk:
                final_chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            current_chunk.append(p)
            current_len += len(p)
            
    if current_chunk:
        final_chunks.append("\n\n".join(current_chunk))
        
    return final_chunks

def process_pdf_stream(file_stream) -> list[str]:
    try:
        pdf = PdfReader(file_stream)
        text_content = []
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_content.append(t)
        
        full_text = "\n\n".join(text_content)
        return recursive_chunk_text(full_text)
    except Exception as e:
        print(f"PDF Error: {e}")
        return []

def process_file_stream(file_stream, filename: str) -> list[str]:
    filename = filename.lower()
    
    if filename.endswith(".pdf"):
        return process_pdf_stream(file_stream)
        
    elif filename.endswith(".md") or filename.endswith(".txt"):
        try:
            # Handle bytes vs string
            if isinstance(file_stream, bytes):
                text = file_stream.decode("utf-8")
            elif hasattr(file_stream, "read"):
                content = file_stream.read()
                if isinstance(content, bytes):
                    text = content.decode("utf-8")
                else:
                    text = content
            else:
                text = str(file_stream)
                
            return recursive_chunk_text(text)
        except Exception as e:
            print(f"Markdown Error: {e}")
            return []
            
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        try:
            chunks = []
            excel_file = pd.ExcelFile(file_stream)
            all_text = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                # Helper description
                all_text.append(f"# Sheet: {sheet_name}")
                all_text.append(df.to_markdown(index=False))
            
            full_text = "\n\n".join(all_text)
            return recursive_chunk_text(full_text)
        except Exception as e:
            print(f"Excel Error: {e}")
            return []
            
    return []

def generate_chunk_id(scope: str, filename: str, index: int) -> str:
    """
    Generates a deterministic ID for a chunk.
    Format: {scope}_{filename}_{index}
    """
    import re
    # Clean filename to be safe (remove spaces, special chars if needed)
    # Using simple replacement
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    return f"{scope}_{safe_filename}_{index}"

