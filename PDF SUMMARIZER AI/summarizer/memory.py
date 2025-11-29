# PDF SUMMARIZER AI/summarizer/memory.py

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class MemoryManager:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        try:
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatIP(self.dimension)
            self.stored_chunks: List[Dict[str, str]] = []
            print(f"✅ Memory Manager initialized with model '{model_name}'.")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to initialize SentenceTransformer. Error: {e}")

    def add_document_chunks(self, chunks: List[str], doc_name: str):
        if not self.model or not chunks: return
        embeddings = self.model.encode(chunks, convert_to_numpy=True)
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        for chunk in chunks:
            self.stored_chunks.append({"document_name": doc_name, "chunk_text": chunk})

    def search_relevant_context(self, query_chunk: str, k: int = 3, threshold: float = 0.5) -> str:
        if not self.model or self.index.ntotal == 0: return ""
        query_embedding = self.model.encode([query_chunk], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        distances, indices = self.index.search(query_embedding, k)
        relevant_context = []
        for i, dist in enumerate(distances[0]):
            if dist >= threshold:
                idx = indices[0][i]
                if idx < len(self.stored_chunks):
                    context = self.stored_chunks[idx]
                    if context["chunk_text"] != query_chunk:
                        relevant_context.append(f"From '{context['document_name']}':\n...{context['chunk_text'][:250]}...")
        return "\n\n---\n\n".join(relevant_context) if relevant_context else ""