"""
search.py — Enhanced search: BM25, fuzzy matching, synonym expansion, scoring
"""

import re
import os
import json
import sqlite3

# ── Synonym store (SQLite-backed) ──────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "tome.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_synonym_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical TEXT NOT NULL,
            variants TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_all_synonym_groups() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM synonyms ORDER BY canonical").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_synonym_group(canonical: str, variants: list[str]):
    conn = get_connection()
    conn.execute(
        "INSERT INTO synonyms (canonical, variants) VALUES (?, ?)",
        (canonical.strip().lower(), json.dumps([v.strip().lower() for v in variants if v.strip()]))
    )
    conn.commit()
    conn.close()


def update_synonym_group(group_id: int, canonical: str, variants: list[str]):
    conn = get_connection()
    conn.execute(
        "UPDATE synonyms SET canonical = ?, variants = ? WHERE id = ?",
        (canonical.strip().lower(), json.dumps([v.strip().lower() for v in variants if v.strip()]), group_id)
    )
    conn.commit()
    conn.close()


def delete_synonym_group(group_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM synonyms WHERE id = ?", (group_id,))
    conn.commit()
    conn.close()


def build_synonym_map() -> dict[str, str]:
    """
    Build a flat map: variant → canonical
    e.g. {"retirement fund": "cpf", "provident fund": "cpf"}
    """
    groups = get_all_synonym_groups()
    synonym_map = {}
    for group in groups:
        canonical = group["canonical"]
        variants = json.loads(group["variants"])
        synonym_map[canonical] = canonical
        for v in variants:
            synonym_map[v] = canonical
    return synonym_map


def expand_query_with_synonyms(query: str) -> str:
    """
    Expand query by replacing known variants with their canonical form,
    and appending canonical + variants as additional search terms.
    """
    synonym_map = build_synonym_map()
    if not synonym_map:
        return query

    expanded_terms = set(query.lower().split())

    # Check each synonym group
    groups = get_all_synonym_groups()
    for group in groups:
        canonical = group["canonical"]
        variants = json.loads(group["variants"])
        all_terms = [canonical] + variants

        # If any term from this group appears in the query, add all terms
        for term in all_terms:
            if term in query.lower():
                for t in all_terms:
                    expanded_terms.add(t)
                break

    return query + " " + " ".join(expanded_terms - set(query.lower().split()))


# ── BM25 FAQ matching ──────────────────────────────────────────────────────────

def bm25_faq_match(query: str, faqs: list[dict], top_k: int = 3) -> list[dict]:
    """
    Use BM25 to rank FAQs against the query.
    Falls back to simple keyword overlap if rank_bm25 not installed.
    """
    if not faqs:
        return []

    try:
        from rank_bm25 import BM25Okapi

        # Tokenize FAQ questions + answers
        corpus = []
        for faq in faqs:
            tokens = re.findall(r'\w+', (faq["question"] + " " + faq["answer"]).lower())
            corpus.append(tokens)

        query_tokens = re.findall(r'\w+', query.lower())
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(query_tokens)

        # Return top_k with scores
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in ranked[:top_k]:
            if score > 0:
                faq = dict(faqs[idx])
                faq["bm25_score"] = float(score)
                results.append(faq)
        return results

    except ImportError:
        # Fallback: keyword overlap
        query_terms = set(re.findall(r'\w+', query.lower()))
        scored = []
        for faq in faqs:
            faq_terms = set(re.findall(r'\w+', (faq["question"] + " " + faq["answer"]).lower()))
            score = len(query_terms & faq_terms)
            if score > 0:
                scored.append((score, faq))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:top_k]]


# ── Fuzzy matching ─────────────────────────────────────────────────────────────

def fuzzy_faq_match(query: str, faqs: list[dict], threshold: int = 70, top_k: int = 3) -> list[dict]:
    """
    Use RapidFuzz to find FAQs matching the query even with typos.
    threshold: minimum similarity score (0-100)
    """
    if not faqs:
        return []

    try:
        from rapidfuzz import fuzz, process

        scored = []
        for faq in faqs:
            # Score against question and answer separately, take best
            q_score = fuzz.token_set_ratio(query, faq["question"])
            a_score = fuzz.token_set_ratio(query, faq["answer"]) * 0.7  # weight answer lower
            best_score = max(q_score, a_score)

            if best_score >= threshold:
                faq_copy = dict(faq)
                faq_copy["fuzzy_score"] = best_score
                scored.append((best_score, faq_copy))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:top_k]]

    except ImportError:
        return []


# ── Combined FAQ matching ──────────────────────────────────────────────────────

def enhanced_faq_match(query: str, faqs: list[dict], top_k: int = 3) -> list[dict]:
    """
    Combines BM25 + fuzzy matching for best FAQ retrieval.
    Deduplicates and merges scores.
    """
    expanded_query = expand_query_with_synonyms(query)

    bm25_results = bm25_faq_match(expanded_query, faqs, top_k=top_k)
    fuzzy_results = fuzzy_faq_match(expanded_query, faqs, threshold=65, top_k=top_k)

    # Merge by FAQ id, keeping best score
    seen = {}
    for faq in bm25_results:
        fid = faq["id"]
        if fid not in seen:
            faq["match_method"] = "bm25"
            seen[fid] = faq

    for faq in fuzzy_results:
        fid = faq["id"]
        if fid not in seen:
            faq["match_method"] = "fuzzy"
            seen[fid] = faq

    return list(seen.values())[:top_k]


# ── Chunk re-ranking ───────────────────────────────────────────────────────────

def rerank_chunks(query: str, chunks: list[dict], synonym_map: dict = None) -> list[dict]:
    """
    Re-rank retrieved chunks using:
    1. Exact phrase match bonus
    2. BM25 score
    3. Fuzzy token overlap
    4. Original semantic score
    Returns chunks with score_explanation added.
    """
    if not chunks:
        return []

    expanded_query = expand_query_with_synonyms(query)
    query_lower = expanded_query.lower()
    query_tokens = re.findall(r'\w+', query_lower)

    # Try BM25 over chunks
    bm25_scores = {}
    try:
        from rank_bm25 import BM25Okapi
        corpus = [re.findall(r'\w+', c["content"].lower()) for c in chunks]
        if corpus and any(corpus):
            bm25 = BM25Okapi(corpus)
            scores = bm25.get_scores(query_tokens)
            for i, score in enumerate(scores):
                bm25_scores[i] = float(score)
    except ImportError:
        pass

    # Try fuzzy scoring
    fuzzy_scores = {}
    try:
        from rapidfuzz import fuzz
        for i, chunk in enumerate(chunks):
            fuzzy_scores[i] = fuzz.token_set_ratio(query, chunk["content"]) / 100.0
    except ImportError:
        pass

    scored_chunks = []
    for i, chunk in enumerate(chunks):
        content_lower = chunk["content"].lower()
        semantic_score = chunk.get("score", 0.5)

        # Exact phrase match
        exact_match = query.lower() in content_lower
        phrase_bonus = 0.3 if exact_match else 0.0

        # BM25
        bm25_score = bm25_scores.get(i, 0)
        bm25_normalized = min(bm25_score / 10.0, 1.0) if bm25_score > 0 else 0

        # Fuzzy
        fuzzy_score = fuzzy_scores.get(i, 0)

        # Combined score
        final_score = (
            semantic_score * 0.4 +
            bm25_normalized * 0.3 +
            fuzzy_score * 0.2 +
            phrase_bonus * 0.1
        )

        # Score explanation
        if exact_match:
            explanation = "Exact phrase match"
            match_color = "#15803d"
        elif semantic_score >= 0.75:
            explanation = "High semantic similarity"
            match_color = "#1d4ed8"
        elif bm25_normalized >= 0.5:
            explanation = "Strong keyword match"
            match_color = "#7e22ce"
        elif fuzzy_score >= 0.7:
            explanation = "Fuzzy match"
            match_color = "#b45309"
        else:
            explanation = "Semantic similarity"
            match_color = "#555"

        chunk = dict(chunk)
        chunk["final_score"] = final_score
        chunk["score_explanation"] = explanation
        chunk["match_color"] = match_color
        chunk["score_pct"] = int(min(final_score * 100, 99))
        scored_chunks.append(chunk)

    scored_chunks.sort(key=lambda x: x["final_score"], reverse=True)
    return scored_chunks


# ── Typo tolerance for query ───────────────────────────────────────────────────

def correct_query_typos(query: str, faqs: list[dict], chunks: list[dict]) -> tuple[str, bool]:
    """
    Detect if query has likely typos by checking similarity against known terms.
    Returns (corrected_query, was_corrected).
    """
    try:
        from rapidfuzz import process, fuzz

        # Build vocabulary from FAQ questions + chunk content
        vocab = set()
        for faq in faqs:
            vocab.update(re.findall(r'\b[a-zA-Z]{4,}\b', faq["question"].lower()))
        for chunk in chunks[:20]:
            vocab.update(re.findall(r'\b[a-zA-Z]{4,}\b', chunk["content"].lower()))

        if not vocab:
            return query, False

        vocab = list(vocab)
        query_words = query.split()
        corrected_words = []
        any_corrected = False

        for word in query_words:
            if len(word) < 4 or not word.isalpha():
                corrected_words.append(word)
                continue

            match, score, _ = process.extractOne(word.lower(), vocab, scorer=fuzz.ratio)
            if score >= 85 and match != word.lower():
                corrected_words.append(match)
                any_corrected = True
            else:
                corrected_words.append(word)

        corrected = " ".join(corrected_words)
        return corrected, any_corrected

    except ImportError:
        return query, False


# ── Phrase highlighting ─────────────────────────────────────────────────────────

def highlight_text(text: str, query: str) -> str:
    """
    Two-level highlighting:
    - Exact phrase match: darker amber (#e07b00)
    - Individual word/stem match: yellow (#ffeb3b)
    """
    if not query or not text:
        return text

    result = text

    # Level 1: Exact phrase (darker highlight)
    phrase = query.strip()
    if len(phrase) > 3:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        result = pattern.sub(
            lambda m: f'<mark style="background:#e07b00;color:#fff;font-weight:bold;padding:0 3px;border-radius:2px;">{m.group(0)}</mark>',
            result
        )

    # Level 2: Individual words (yellow), skip already-highlighted
    query_words = [w for w in re.findall(r'\w+', query.lower()) if len(w) >= 3]
    style = "background:#ffeb3b;font-weight:bold;padding:0 2px;"

    def stem(word):
        w = word.lower()
        for suffix in ['tion', 'ment', 'ness', 'able', 'ible', 'ing', 'ed', 'er', 'est', 'ly', 's']:
            if w.endswith(suffix) and len(w) - len(suffix) > 2:
                return w[:-len(suffix)]
        return w

    def stems_match(qw, tw):
        if len(qw) < 3 or len(tw) < 3:
            return qw.lower() == tw.lower()
        qs, ts = stem(qw), stem(tw)
        if len(qs) < 3 or len(ts) < 3:
            return qs == ts
        return qs.startswith(ts) or ts.startswith(qs)

    def word_replacer(match):
        word = match.group(0)
        if len(word) < 3:
            return word
        if any(stems_match(qw, word) for qw in query_words):
            return f'<mark style="{style}">{word}</mark>'
        return word

    # Only apply word highlighting outside existing <mark> tags
    result = re.sub(r'(?<![>])\b([A-Za-z0-9]+)\b(?![^<]*>)', word_replacer, result)
    return result
