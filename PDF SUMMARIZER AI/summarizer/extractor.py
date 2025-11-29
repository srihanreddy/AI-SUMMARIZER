# PDF SUMMARIZER AI/summarizer/extractor.py

import fitz # PyMuPDF
import re
from summarizer.parser import count_tokens

def extract_all_data_by_page(pdf_path: str) -> list[dict]:
    """Extracts text from each page of a PDF."""
    page_data = []
    try:
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                page_text = page.get_text("text")
                if page_text.strip():
                    page_data.append({"page": page_num, "text": page_text})
    except Exception as e:
        print(f"❌ Failed to process PDF '{pdf_path}': {e}")
    return page_data

def intelligent_chunking(pages: list[dict], token_limit: int = 3500) -> list[tuple[str, str]]:
    """
    Chunks a document by semantic units (paragraphs) to preserve context.
    Returns a list of tuples, where each tuple is (chunk_text, page_label).
    """
    chunks = []
    current_chunk = []
    current_tokens = 0
    page_range = [pages[0]['page'], pages[0]['page']]

    for page in pages:
        page_range[1] = page['page']
        # Split text into paragraphs (or lines if no double newline)
        paragraphs = re.split(r'\n\s*\n', page['text'])
        
        for para in paragraphs:
            para_tokens = count_tokens(para)
            if current_tokens + para_tokens > token_limit and current_chunk:
                # Finalize the current chunk
                chunk_text = "\n\n".join(current_chunk)
                page_label = f"{page_range[0]}-{page_range[1]}" if page_range[0] != page_range[1] else f"{page_range[0]}"
                chunks.append((chunk_text, page_label))
                
                # Start a new chunk
                current_chunk = [para]
                current_tokens = para_tokens
                page_range = [page['page'], page['page']]
            else:
                current_chunk.append(para)
                current_tokens += para_tokens

    # Add the last remaining chunk
    if current_chunk:
        chunk_text = "\n\n".join(current_chunk)
        page_label = f"{page_range[0]}-{page_range[1]}" if page_range[0] != page_range[1] else f"{page_range[0]}"
        chunks.append((chunk_text, page_label))
        
    return chunks