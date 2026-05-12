"""
app.py — Tome: AI Knowledge Base for Call Center Agents
"""

import streamlit as st
import os
import sys
import re

sys.path.insert(0, os.path.dirname(**file**))
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

_params = st.query_params
if "q" in _params and not st.session_state.last_query:
st.session_state.last_query = _params["q"]

# ── Helper functions ───────────────────────────────────────────────────────────

def _keyword_faq_match(query, faqs):
query_terms = set(query.lower().split())
scored = []

```
for faq in faqs:
    faq_terms = set(faq["question"].lower().split())
    score = len(query_terms & faq_terms)

    if score > 0:
        scored.append((score, faq))

scored.sort(key=lambda x: x[0], reverse=True)
return [f for _, f in scored[:3]]
```

def _run_search(query):
chunks = ingestion.hybrid_search(query, top_k=5)
faqs = db.get_all_faqs()
matched_faqs = _keyword_faq_match(query, faqs)

```
return {
    "chunks": chunks,
    "matched_faqs": matched_faqs,
    "mode": "search"
}
```

def _run_ai(query):
chunks = ingestion.hybrid_search(query, top_k=5)
result = ai.generate_answer(query, chunks)
result["chunks"] = chunks

```
faqs = db.get_all_faqs()
result["matched_faqs"] = ai.search_faqs(query, faqs) if faqs else []
result["mode"] = "ai"

return result
```

def _extract_qa(chunk_text):
lines_split = chunk_text.split('\n')
question = ""
answer_lines = []

```
for i, line in enumerate(lines_split):
    if line.startswith('##') or line.startswith('# '):
        question = line.lstrip('#').strip()
        answer_lines = lines_split[i + 1:]
        break

cleaned = [
    l.strip()
    for l in answer_lines
    if l.strip() and not l.strip().startswith('#')
]

return question, '\n'.join(cleaned)
```

def _highlight_matching_words(text, query):
if not text or not query:
return text

```
escaped_query = re.escape(query.strip())

text = re.sub(
    escaped_query,
    lambda m: f'<mark style="background:#ffd54f;">{m.group(0)}</mark>',
    text,
    flags=re.IGNORECASE
)

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
```

def _format_answer_bullets(text):
raw_lines = text.split('\n')
bullets = []

```
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
```

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
st.markdown('## 📚 Tome')

# ═══════════════════════════════════════════════════════════════════════════════

# SEARCH PAGE

# ═══════════════════════════════════════════════════════════════════════════════

query = st.text_input(
"Search query",
placeholder="e.g. CPF investment account number"
)

if query:

```
result = _run_search(query)
chunks = result.get("chunks", [])

st.markdown("## Results")

for chunk in chunks:

    score_pct = int(chunk.get("score", 0) * 100)

    question, answer = _extract_qa(chunk["content"])

    title = question if question else chunk.get("title", "Result")

    highlighted_title = _highlight_matching_words(
        title,
        query
    )

    with st.expander(f"{title} — {score_pct}% match"):

        st.markdown(
            f'''
            <div style="font-weight:600; font-size:1rem; margin-bottom:0.5rem;">
                ❓ {highlighted_title}
            </div>
            ''',
            unsafe_allow_html=True
        )

        text_to_display = answer if answer else chunk["content"]

        highlighted = _highlight_matching_words(
            text_to_display,
            query
        )

        bullets = _format_answer_bullets(highlighted)

        st.markdown(bullets, unsafe_allow_html=True)

if result.get("matched_faqs"):

    st.markdown("## Related FAQs")

    for faq in result["matched_faqs"]:

        highlighted_question = _highlight_matching_words(
            faq['question'],
            query
        )

        highlighted_answer = _highlight_matching_words(
            faq['answer'],
            query
        )

        st.markdown(f'''
        <div style="
            background:#FFFFFF;
            border:1px solid #E5E0D8;
            border-radius:8px;
            padding:1rem 1.2rem;
            margin:0.6rem 0;
        ">
            <div style="font-weight:600; margin-bottom:0.4rem;">
                ❓ {highlighted_question}
            </div>

            <div style="color:#555; line-height:1.6;">
                {highlighted_answer}
            </div>
        </div>
        ''', unsafe_allow_html=True)
```
