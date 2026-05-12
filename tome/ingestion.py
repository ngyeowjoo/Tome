"""
modules/ingestion.py — Document parsing, chunking, and embedding for Tome
"""

import os
import re
import pickle
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "faiss_index", "index.faiss")
EMBEDDINGS_PATH = os.path.join(DATA_DIR, "faiss_index", "embeddings.pkl")

# ── Lazy-loaded globals ────────────────────────────────────────────────────────

_model = None
_faiss_index = None
_embedding_store: list[np.ndarray] = []   # parallel list to FAISS ids


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_faiss_index(dim: int = 384):
    global _faiss_index, _embedding_store
    import faiss
    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)

    if os.path.exists(FAISS_INDEX_PATH):
        _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        if os.path.exists(EMBEDDINGS_PATH):
            with open(EMBEDDINGS_PATH, "rb") as f:
                _embedding_store = pickle.load(f)
    else:
        _faiss_index = faiss.IndexFlatL2(dim)
        _embedding_store = []

    return _faiss_index


def _save_index():
    import faiss
    if _faiss_index is not None:
        faiss.write_index(_faiss_index, FAISS_INDEX_PATH)
        with open(EMBEDDINGS_PATH, "wb") as f:
            pickle.dump(_embedding_store, f)


def get_index_size() -> int:
    idx = _get_faiss_index()
    return idx.ntotal


# ── Text extraction ────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    import fitz  # PyMuPDF
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def extract_text_from_docx(file_bytes: bytes) -> str:
    import io
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text_from_xlsx(file_bytes: bytes) -> str:
    import io
    import pandas as pd
    xl = pd.ExcelFile(io.BytesIO(file_bytes))
    parts = []
    for sheet in xl.sheet_names:
        df = xl.parse(sheet).fillna("")
        parts.append(f"[Sheet: {sheet}]\n{df.to_string(index=False)}")
    return "\n\n".join(parts)


def extract_text(file_bytes: bytes, file_type: str) -> str:
    ft = file_type.lower()
    if ft == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ft in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    elif ft in ("xlsx", "xls"):
        return extract_text_from_xlsx(file_bytes)
    elif ft == "md":
        # Markdown is just plain text
        return file_bytes.decode('utf-8', errors='ignore')
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


# ── Chunking ───────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """
    Split text into chunks while respecting section boundaries.
    - Treats # and ## headings as natural break points
    - Treats --- as hard section dividers
    - Falls back to word-count chunking within sections
    """
    import re
    
    # Split by hard dividers (---)
    sections = re.split(r'\n\s*---+\s*\n', text)
    
    all_chunks = []
    
    for section in sections:
        if not section.strip():
            continue
        
        # Split section by headings (# or ##)
        subsections = re.split(r'\n(#{1,2}\s+.+)\n', section)
        
        for i, subsection in enumerate(subsections):
            if not subsection.strip():
                continue
            
            # If this looks like a heading (starts with #), keep it with next content
            is_heading = subsection.strip().startswith('#')
            
            if is_heading and i + 1 < len(subsections):
                # Combine heading with its content
                combined = subsection + "\n" + subsections[i + 1]
                subsections[i + 1] = ""  # Mark as processed
                subsection = combined
            
            if not subsection.strip():
                continue
            
            # Now chunk this subsection by word count
            words = subsection.split()
            if len(words) < 20:
                # If subsection is too small, keep it as-is
                all_chunks.append(subsection.strip())
            else:
                # Chunk into word-count pieces
                chunk_start = 0
                while chunk_start < len(words):
                    chunk_end = min(chunk_start + chunk_size, len(words))
                    chunk = " ".join(words[chunk_start:chunk_end])
                    if len(chunk.strip()) > 20:
                        all_chunks.append(chunk.strip())
                    chunk_start += chunk_size - overlap
    
    return all_chunks


# ── Embedding + FAISS ──────────────────────────────────────────────────────────

def embed_and_store(chunks: list[str], document_id: int) -> list[int]:
    """
    Embed chunks, add to FAISS index, persist.
    Returns list of embedding indices (FAISS row ids) for each chunk.
    """
    import db

    model = _get_model()
    idx = _get_faiss_index()

    embeddings = model.encode(chunks, show_progress_bar=False, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype=np.float32)

    start_id = idx.ntotal
    idx.add(embeddings)

    embedding_indices = list(range(start_id, start_id + len(chunks)))
    _embedding_store.extend(embeddings)
    _save_index()

    # Persist chunks to SQLite
    for i, (chunk, emb_idx) in enumerate(zip(chunks, embedding_indices)):
        db.insert_chunk(document_id, chunk, i, emb_idx)

    return embedding_indices


# ── Full ingestion pipeline ────────────────────────────────────────────────────

def ingest_file(file_bytes: bytes, filename: str) -> dict:
    """
    Full pipeline: parse → chunk → embed → store.
    Returns summary dict.
    """
    import db

    ext = filename.rsplit(".", 1)[-1].lower()
    title = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()

    # Extract
    text = extract_text(file_bytes, ext)
    if not text.strip():
        raise ValueError("No text could be extracted from this file.")

    # Chunk
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("Document produced no usable text chunks.")

    # Store document record
    doc_id = db.insert_document(title, filename, ext)

    # Embed + store
    embedding_indices = embed_and_store(chunks, doc_id)

    return {
        "doc_id": doc_id,
        "title": title,
        "chunks": len(chunks),
        "embedding_indices": embedding_indices,
    }


# ── Keyword search helper ──────────────────────────────────────────────────────

def keyword_search(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Simple BM25-style keyword scoring over chunk content."""
    query_terms = set(re.findall(r"\w+", query.lower()))
    scored = []
    for chunk in chunks:
        content_words = set(re.findall(r"\w+", chunk["content"].lower()))
        score = len(query_terms & content_words)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


# ── Semantic search ────────────────────────────────────────────────────────────

def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """FAISS nearest-neighbour search. Returns chunk dicts with scores."""
    import db

    idx = _get_faiss_index()
    if idx.ntotal == 0:
        return []

    model = _get_model()
    q_embedding = model.encode([query], normalize_embeddings=True)
    q_embedding = np.array(q_embedding, dtype=np.float32)

    distances, indices = idx.search(q_embedding, min(top_k, idx.ntotal))
    embedding_indices = [int(i) for i in indices[0] if i >= 0]

    chunks = db.get_chunks_by_ids(embedding_indices)

    # Attach distance score
    dist_map = {int(indices[0][i]): float(distances[0][i]) for i in range(len(indices[0]))}
    for chunk in chunks:
        chunk["score"] = 1 / (1 + dist_map.get(chunk["embedding_index"], 999))

    chunks.sort(key=lambda x: x["score"], reverse=True)
    return chunks


# ── Hybrid search ──────────────────────────────────────────────────────────────

def hybrid_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Combines keyword + semantic results, deduplicates, returns top_k.
    """
    import db

    semantic_results = semantic_search(query, top_k=top_k)
    all_chunks = db.get_all_chunks()
    keyword_results = keyword_search(query, all_chunks, top_k=top_k)

    # Merge by chunk id, semantic results take priority
    seen_ids = set()
    merged = []
    for chunk in semantic_results:
        if chunk["id"] not in seen_ids:
            chunk["source"] = "semantic"
            merged.append(chunk)
            seen_ids.add(chunk["id"])

    for chunk in keyword_results:
        if chunk["id"] not in seen_ids:
            chunk["source"] = "keyword"
            chunk["score"] = chunk.get("score", 0.5)
            merged.append(chunk)
            seen_ids.add(chunk["id"])

    return merged[:top_k]
