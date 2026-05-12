"""
app.py — Tome: AI Knowledge Base for Call Center Agents
Run with: streamlit run app.py
"""

import streamlit as st
import os
import sys

# Ensure modules are importable
sys.path.insert(0, os.path.dirname(__file__))

import db, ingestion, ai

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Tome — Knowledge Base",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #F5F2EB !important;
    border-right: 1px solid #E0DAD0;
}

/* Main bg */
.stApp {
    background: #FAFAF7;
}

/* Metric cards */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #E5E0D8;
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    color: #C4992A;
    line-height: 1;
}
.metric-label {
    font-size: 0.75rem;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.4rem;
}

/* Answer card */
.answer-card {
    background: #FFFFFF;
    border: 1px solid #E5E0D8;
    border-left: 3px solid #C4992A;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

/* Source card */
.source-card {
    background: #FAFAF7;
    border: 1px solid #E8E3DA;
    border-radius: 6px;
    padding: 0.9rem 1.1rem;
    margin: 0.5rem 0;
    font-size: 0.875rem;
}
.source-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #C4992A;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
}

/* Confidence badge */
.conf-high { color: #16a34a; font-weight: 600; }
.conf-medium { color: #d97706; font-weight: 600; }
.conf-low { color: #dc2626; font-weight: 600; }

/* FAQ card */
.faq-card {
    background: #FFFFFF;
    border: 1px solid #E5E0D8;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.faq-q {
    font-weight: 600;
    color: #1A1A1A;
    margin-bottom: 0.4rem;
}
.faq-a {
    color: #555;
    font-size: 0.9rem;
    line-height: 1.6;
}

/* Logo */
.tome-logo {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #C4992A;
    letter-spacing: -0.02em;
}
.tome-sub {
    font-size: 0.7rem;
    color: #AAA;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-top: -4px;
}

/* Search box */
.stTextInput > div > div > input {
    background: #FFFFFF !important;
    border: 1px solid #D8D3CA !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 1rem !important;
    color: #1A1A1A !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #C4992A !important;
    box-shadow: 0 0 0 2px rgba(196, 153, 42, 0.15) !important;
}

/* Buttons */
.stButton > button {
    background: #C4992A !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #A87E20 !important;
    transform: translateY(-1px) !important;
}

/* Section headers */
.section-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #AAA;
    border-bottom: 1px solid #E5E0D8;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* Tag badge */
.tag {
    display: inline-block;
    background: #F0EDE6;
    border: 1px solid #DDD8CE;
    border-radius: 4px;
    padding: 0.15rem 0.5rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #888;
    margin-right: 0.3rem;
}

/* Dividers */
hr { border-color: #E5E0D8 !important; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #E5E0D8;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: #AAA !important;
    background: transparent !important;
    border-radius: 0 !important;
    padding: 0.6rem 1.2rem !important;
}
.stTabs [aria-selected="true"] {
    color: #C4992A !important;
    border-bottom: 2px solid #C4992A !important;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    color: #888 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F0EDE6; }
::-webkit-scrollbar-thumb { background: #CCC; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────

db.init_db()

# ── Session state ──────────────────────────────────────────────────────────────

if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = False
if "ai_mode" not in st.session_state:
    st.session_state.ai_mode = False  # Default: search-only mode

# ── Query param pre-fill (from Chrome extension / embed) ──────────────────────
_params = st.query_params
if "q" in _params and not st.session_state.last_query:
    st.session_state.last_query = _params["q"]

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="tome-logo">📚 Tome</div>', unsafe_allow_html=True)
    st.markdown('<div class="tome-sub">Knowledge Base</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    nav = st.radio(
        "Navigation",
        ["🔍 Search", "📋 FAQs", "📂 Admin", "📊 Analytics"],
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">System Status</div>', unsafe_allow_html=True)

    chunk_count = db.get_chunk_count()
    doc_count = len(db.get_all_documents())
    faq_count = len(db.get_all_faqs())

    st.markdown(f"""
    <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #888; line-height: 2;">
    📄 {doc_count} document{'s' if doc_count != 1 else ''}<br>
    🧩 {chunk_count} chunk{'s' if chunk_count != 1 else ''} indexed<br>
    ❓ {faq_count} FAQ{'s' if faq_count != 1 else ''}
    </div>
    """, unsafe_allow_html=True)

    if chunk_count == 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.warning("⚠️ No documents indexed yet. Go to **Admin** to upload content.", icon="⚠️")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Search Mode</div>', unsafe_allow_html=True)

    ai_mode = st.toggle(
        "AI Answer Generation",
        value=st.session_state.ai_mode,
        help="Off: fast keyword+semantic search, no API needed. On: Claude generates a summarised answer.",
    )
    if ai_mode != st.session_state.ai_mode:
        st.session_state.ai_mode = ai_mode
        st.session_state.last_result = None
        st.session_state.last_query = ""
        st.rerun()

    if st.session_state.ai_mode:
        st.markdown('<p style="font-family:IBM Plex Mono,monospace; font-size:0.7rem; color:#C4992A;">⚡ AI mode — uses Anthropic API</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="font-family:IBM Plex Mono,monospace; font-size:0.7rem; color:#16a34a;">✓ Search mode — no API needed</p>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def _keyword_faq_match(query, faqs):
    """Simple keyword overlap FAQ matching — no AI needed."""
    query_terms = set(query.lower().split())
    scored = []
    for faq in faqs:
        faq_terms = set(faq["question"].lower().split())
        score = len(query_terms & faq_terms)
        if score > 0:
            scored.append((score, faq))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:3]]


def _run_search(query):
    chunks = ingestion.hybrid_search(query, top_k=5)
    faqs = db.get_all_faqs()
    matched_faqs = _keyword_faq_match(query, faqs)
    return {"chunks": chunks, "matched_faqs": matched_faqs, "mode": "search"}


def _run_ai(query):
    chunks = ingestion.hybrid_search(query, top_k=5)
    result = ai.generate_answer(query, chunks)
    result["chunks"] = chunks
    faqs = db.get_all_faqs()
    result["matched_faqs"] = ai.search_faqs(query, faqs) if faqs else []
    result["mode"] = "ai"
    return result


def _extract_qa(chunk_text):
    """Extract question and answer from chunk, removing markdown headings."""
    lines_split = chunk_text.split('\n')
    question = ""
    answer_lines = []

    for i, line in enumerate(lines_split):
        if line.startswith('##') or line.startswith('# '):
            question = line.lstrip('#').strip()
            answer_lines = lines_split[i+1:]
            break

    # Keep lines but strip markdown headings and blank lines
    cleaned = [l.strip() for l in answer_lines if l.strip() and not l.strip().startswith('#')]
    answer = '\n'.join(cleaned)
    return question, answer


def _format_answer_bullets(text):
    """Convert answer text into bullet points, splitting on newlines and sentences."""
    import re
    raw_lines = text.split('\n')
    bullets = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        parts = re.split(r'(?<=[.!?])\s+', line)
        for part in parts:
            part = part.strip()
            if len(part) > 10:
                bullets.append(f"<div style='margin-bottom:0.4rem;'>• {part}</div>")
    return "\n".join(bullets)




def _highlight_matching_words(text, query):
    """Highlight matching words with yellow background and bold."""
    import re
    query_words = set(w.lower() for w in re.findall(r"\w+", query))
    def replacer(match):
        word = match.group(0)
        if word.lower() in query_words:
            return f"<mark style=\"background:#ffeb3b;font-weight:bold;padding:0 2px;\">{word}</mark>"
        return word
    result = re.sub(r"(?<![>])\b([A-Za-z0-9]+)\b(?![^<]*>)", replacer, text)
    return result
