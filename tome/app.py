# Updated `tome.py`

```python
"""
app.py — Tome: AI Knowledge Base for Call Center Agents
"""

import streamlit as st
import os
import sys
import re

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
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
[data-testid="stSidebar"] { background: #F5F2EB !important; border-right: 1px solid #E0DAD0; }
.stApp { background: #FAFAF7; }
.metric-card { background:#FFFFFF; border:1px solid #E5E0D8; border-radius:8px; padding:1.2rem 1.5rem; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.05); }
.metric-value { font-family:'IBM Plex Mono',monospace; font-size:2rem; font-weight:600; color:#C4992A; line-height:1; }
.metric-label { font-size:0.75rem; color:#999; text-transform:uppercase; letter-spacing:0.1em; margin-top:0.4rem; }
.answer-card { background:#FFFFFF; border:1px solid #E5E0D8; border-left:3px solid #C4992A; border-radius:8px; padding:1.5rem; margin:1rem 0; box-shadow:0 1px 4px rgba(0,0,0,0.06); }
.faq-card { background:#FFFFFF; border:1px solid #E5E0D8; border-radius:8px; padding:1rem 1.2rem; margin:0.6rem 0; }
.faq-q { font-weight:600; color:#1A1A1A; margin-bottom:0.4rem; }
.faq-a { color:#555; font-size:0.9rem; line-height:1.6; }
.tome-logo { font-family:'IBM Plex Mono',monospace; font-size:1.6rem; font-weight:600; color:#C4992A; letter-spacing:-0.02em; }
.tome-sub { font-size:0.7rem; color:#AAA; text-transform:uppercase; letter-spacing:0.15em; margin-top:-4px; }
.section-header { font-family:'IBM Plex Mono',monospace; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.15em; color:#AAA; border-bottom:1px solid #E5E0D8; padding-bottom:0.5rem; margin-bottom:1rem; }
.tag { display:inline-block; background:#F0EDE6; border:1px solid #DDD8CE; border-radius:4px; padding:0.15rem 0.5rem; font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#888; margin-right:0.3rem; }
.conf-high { color:#16a34a; font-weight:600; }
.conf-medium { color:#d97706; font-weight:600; }
.conf-low { color:#dc2626; font-weight:600; }
hr { border-color:#E5E0D8 !important; }
.stTextInput > div > div > input { background:#FFFFFF !important; border:1px solid #D8D3CA !important; border-radius:8px !important; font-size:1rem !important; color:#1A1A1A !important; padding:0.75rem 1rem !important; }
.stTextInput > div > div > input:focus { border-color:#C4992A !important; box-shadow:0 0 0 2px rgba(196,153,42,0.15) !important; }
.stButton > button { background:#C4992A !important; color:#FFFFFF !important; border:none !important; border-radius:6px !important; font-family:'IBM Plex Mono',monospace !important; font-weight:600 !important; font-size:0.85rem !important; padding:0.5rem 1.2rem !important; }
.stButton > button:hover { background:#A87E20 !important; }
.stTabs [data-baseweb="tab-list"] { background:transparent; border-bottom:1px solid #E5E0D8; }
.stTabs [data-baseweb="tab"] { font-family:'IBM Plex Mono',monospace !important; font-size:0.75rem !important; text-transform:uppercase !important; color:#AAA !important; background:transparent !important; border-radius:0 !important; padding:0.6rem 1.2rem !important; }
.stTabs [aria-selected="true"] { color:#C4992A !important; border-bottom:2px solid #C4992A !important; }
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:#F0EDE6; }
::-webkit-scrollbar-thumb { background:#CCC; border-radius:3px; }
mark {
    background:#ffeb3b;
    padding:0 2px;
    border-radius:2px;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# ── Init DB ────────────────────────────────────────────────────────────────────

db.init_db()

# ── Session state ──────────────────────────────────────────────────────────────

if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = False
if "ai_mode" not in st.session_state:
    st.session_state.ai_mode = False

# Pre-fill from URL query param (Chrome extension)
_params = st.query_params
if "q" in _params and not st.session_state.last_query:
    st.session_state.last_query = _params["q"]

# ── Helper functions ───────────────────────────────────────────────────────────

def _keyword_faq_match(query, faqs):
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
    lines_split = chunk_text.split('\n')
    question = ""
    answer_lines = []

    for i, line in enumerate(lines_split):
        if line.startswith('##') or line.startswith('# '):
            question = line.lstrip('#').strip()
            answer_lines = lines_split[i+1:]
            break

    cleaned = [
        l.strip() for l in answer_lines
        if l.strip() and not l.strip().startswith('#')
    ]

    return question, '\n'.join(cleaned)


def _highlight_matching_words(text, query):
    if not text or not query:
        return text

    # Highlight exact phrase first
    escaped_query = re.escape(query.strip())

    text = re.sub(
        escaped_query,
        lambda m: f'<mark style="background:#ffd54f;">{m.group(0)}</mark>',
        text,
        flags=re.IGNORECASE
    )

    # Highlight individual words
    query_words = [
        re.escape(w)
        for w in re.findall(r"\w+", query)
        if len(w.strip()) > 1
    ]

    if not query_words:
        return text

    pattern = r"(" + "|".join(query_words) + r")"

    return re.sub(
        pattern,
        r'<mark>\1</mark>',
        text,
        flags=re.IGNORECASE,
    )


def _format_answer_bullets(text):
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
                bullets.append(
                    f'<div style="margin-bottom:0.4rem;">• {part}</div>'
                )

    return "\n".join(bullets)

# ==========================================================
# SEARCH RESULTS HIGHLIGHTING CHANGES
# ==========================================================

# Replace your existing search result rendering sections
# with the following updated blocks.

# ----------------------------------------------------------
# SEARCH MODE RESULTS
# ----------------------------------------------------------

"""
Replace this block:

with st.expander(f"❓ {title}  —  {score_pct}% match"):

with the updated version below.
"""

highlighted_title = _highlight_matching_words(
    title,
    st.session_state.last_query
)

with st.expander(f"{title}  —  {score_pct}% match"):
    st.markdown(
        f'''
        <div style="font-weight:600; font-size:1rem; margin-bottom:0.5rem;">
            ❓ {highlighted_title}
        </div>
        ''',
        unsafe_allow_html=True
    )

    st.markdown(src_badge, unsafe_allow_html=True)
    st.markdown("")

    text_to_display = answer if answer else chunk["content"]

    highlighted = _highlight_matching_words(
        text_to_display,
        st.session_state.last_query
    )

    bullets = _format_answer_bullets(highlighted)

    st.markdown(bullets, unsafe_allow_html=True)

    st.markdown(
        f'''
        <p style="font-size:0.75rem; color:#999; margin-top:1rem;
        border-top:1px solid #eee; padding-top:0.5rem;">
            📄 Source: <strong>{chunk.get("title", "Document")}</strong>
        </p>
        ''',
        unsafe_allow_html=True
    )

# ----------------------------------------------------------
# AI MODE SOURCE RESULTS
# ----------------------------------------------------------

"""
Replace this block:

with st.expander(f"📄 {title}  —  {score_pct}% match"):

with the updated version below.
"""

highlighted_title = _highlight_matching_words(
    title,
    st.session_state.last_query
)

with st.expander(f"{title}  —  {score_pct}% match"):
    st.markdown(
        f'''
        <div style="font-weight:600; font-size:1rem; margin-bottom:0.5rem;">
            📄 {highlighted_title}
        </div>
        ''',
        unsafe_allow_html=True
    )

    st.markdown(src_badge, unsafe_allow_html=True)

    highlighted_answer = _highlight_matching_words(
        answer if answer else chunk["content"],
        st.session_state.last_query
    )

    st.markdown(highlighted_answer, unsafe_allow_html=True)

# ----------------------------------------------------------
# AI GENERATED ANSWER HIGHLIGHTING
# ----------------------------------------------------------

"""
Replace this:

<div style="color:#1A1A1A; line-height:1.7; font-size:0.95rem;">
    {result['answer'].replace(chr(10), '<br>')}
</div>

with this.
"""

highlighted_ai_answer = _highlight_matching_words(
    result['answer'],
    st.session_state.last_query
).replace(chr(10), '<br>')

st.markdown(f'''
<div class="answer-card">
    <div style="display:flex; justify-content:space-between;
    align-items:flex-start; margin-bottom:0.8rem;">

        <span style="font-family:monospace; font-size:0.7rem;
        color:#555; text-transform:uppercase; letter-spacing:0.1em;">
            Generated by Claude
        </span>

        <span class="{conf_class}"
        style="font-family:monospace; font-size:0.75rem;">
            ◆ {conf_label} CONFIDENCE ({conf_score}%)
        </span>
    </div>

    <div style="color:#1A1A1A; line-height:1.7; font-size:0.95rem;">
        {highlighted_ai_answer}
    </div>
</div>
''', unsafe_allow_html=True)

# ----------------------------------------------------------
# FAQ HIGHLIGHTING
# ----------------------------------------------------------

"""
Replace this:

<div class="faq-q">❓ {faq['question']}</div>
<div class="faq-a">{faq['answer']}</div>

with this.
"""

st.markdown(f'''
<div class="faq-card">

    <div class="faq-q">
        ❓ {_highlight_matching_words(
            faq['question'],
            st.session_state.last_query
        )}
    </div>

    <div class="faq-a">
        {_highlight_matching_words(
            faq['answer'],
            st.session_state.last_query
        )}
    </div>

</div>
''', unsafe_allow_html=True)

```
