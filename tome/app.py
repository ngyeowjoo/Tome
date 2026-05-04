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


if nav == "🔍 Search":
    if st.session_state.ai_mode:
        st.markdown("## AI Answer")
        st.markdown('<p style="color:#666; font-size:0.9rem;">Claude reads retrieved sources and generates a summarised answer.</p>', unsafe_allow_html=True)
    else:
        st.markdown("## Search")
        st.markdown('<p style="color:#666; font-size:0.9rem;">Hybrid keyword + semantic search — no AI, no API key needed.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input(
            "Search query",
            placeholder="e.g. How do I process a refund for a cancelled subscription?",
            label_visibility="collapsed",
            key="search_input",
        )
    with col2:
        search_clicked = st.button("Search →", use_container_width=True)

    if (query and query != st.session_state.last_query) or (search_clicked and query):
        st.session_state.feedback_given = False
        st.session_state.last_query = query
        msg = "Searching + generating answer..." if st.session_state.ai_mode else "Searching knowledge base..."
        with st.spinner(msg):
            try:
                result = _run_ai(query) if st.session_state.ai_mode else _run_search(query)
                db.log_search(query, len(result.get("chunks", [])))
                st.session_state.last_result = result
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.last_result = None

    if st.session_state.last_result and st.session_state.last_query:
        result = st.session_state.last_result
        chunks = result.get("chunks", [])

        # AI answer block (AI mode only)
        if result.get("mode") == "ai":
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">AI Answer</div>', unsafe_allow_html=True)
            conf_label = result.get("confidence_label", "MEDIUM")
            conf_class = f"conf-{conf_label.lower()}"
            conf_score = int(result.get("confidence", 0.5) * 100)
            st.markdown(f"""
            <div class="answer-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.8rem;">
                    <span style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#555; text-transform:uppercase; letter-spacing:0.1em;">Generated by Claude</span>
                    <span class="{conf_class}" style="font-family:'IBM Plex Mono',monospace; font-size:0.75rem;">◆ {conf_label} CONFIDENCE ({conf_score}%)</span>
                </div>
                <div style="color:#1A1A1A; line-height:1.7; font-size:0.95rem;">{result['answer'].replace(chr(10), '<br>')}</div>
            </div>
            """, unsafe_allow_html=True)

            if not st.session_state.feedback_given:
                st.markdown('<div style="font-size:0.8rem; color:#666; margin-bottom:0.4rem;">Was this helpful?</div>', unsafe_allow_html=True)
                fb1, fb2, _ = st.columns([1, 1, 8])
                with fb1:
                    if st.button("👍 Yes"):
                        db.insert_feedback(st.session_state.last_query, result["answer"][:300], 1)
                        st.session_state.feedback_given = True
                        st.rerun()
                with fb2:
                    if st.button("👎 No"):
                        db.insert_feedback(st.session_state.last_query, result["answer"][:300], -1)
                        st.session_state.feedback_given = True
                        st.rerun()
            else:
                st.markdown('<p style="font-size:0.75rem; color:#16a34a;">✓ Feedback recorded — thank you</p>', unsafe_allow_html=True)

        # Results / sources
        if chunks:
            st.markdown("<br>", unsafe_allow_html=True)
            header = "Top Results" if result.get("mode") == "search" else "Supporting Sources"
            st.markdown(f'<div class="section-header">{header}</div>', unsafe_allow_html=True)

            if result.get("mode") == "search":
                for chunk in chunks:
                    src_badge = '<span class="tag">semantic</span>' if chunk.get("source") == "semantic" else '<span class="tag">keyword</span>'
                    score_pct = int(chunk.get("score", 0) * 100)
                    st.markdown(f"""
                    <div class="answer-card" style="margin-bottom:0.8rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                            <span style="font-weight:600; color:#1A1A1A; font-size:0.9rem;">📄 {chunk.get('title', 'Document')}</span>
                            <div>{src_badge} <span style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#888;">match {score_pct}%</span></div>
                        </div>
                        <div style="color:#333; font-size:0.875rem; line-height:1.7;">{chunk['content'][:400]}{"..." if len(chunk['content']) > 400 else ""}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                for chunk in chunks[:4]:
                    src_badge = '<span class="tag">semantic</span>' if chunk.get("source") == "semantic" else '<span class="tag">keyword</span>'
                    score_pct = int(chunk.get("score", 0) * 100)
                    with st.expander(f"📄 {chunk.get('title', 'Document')} — match {score_pct}%"):
                        st.markdown(f'{src_badge}', unsafe_allow_html=True)
                        st.markdown(f'<div style="color:#222; font-size:0.875rem; line-height:1.7; margin-top:0.5rem;">{chunk["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("No matching content found. Try different keywords or upload more documents.")

        # Related FAQs
        if result.get("matched_faqs"):
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">Related FAQs</div>', unsafe_allow_html=True)
            for faq in result["matched_faqs"]:
                st.markdown(f"""
                <div class="faq-card">
                    <div class="faq-q">❓ {faq['question']}</div>
                    <div class="faq-a">{faq['answer']}</div>
                </div>
                """, unsafe_allow_html=True)

    elif not st.session_state.last_query:
        st.markdown("<br>" * 3, unsafe_allow_html=True)
        icon = "🤖" if st.session_state.ai_mode else "🔍"
        label = "Ask a question to generate an AI answer" if st.session_state.ai_mode else "Start typing to search the knowledge base"
        st.markdown(f"""
        <div style="text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">{icon}</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.15em; color:#888;">{label}</div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FAQs PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif nav == "📋 FAQs":
    st.markdown("## Frequently Asked Questions")
    st.markdown('<p style="color:#666; font-size:0.9rem;">Browse or manage structured Q&A pairs.</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Browse FAQs", "Add FAQ"])

    with tab1:
        faqs = db.get_all_faqs()
        if not faqs:
            st.info("No FAQs yet. Add some in the 'Add FAQ' tab.")
        else:
            # Group by category
            categories = {}
            for faq in faqs:
                cat = faq.get("category", "General")
                categories.setdefault(cat, []).append(faq)

            for cat, items in categories.items():
                st.markdown(f'<div class="section-header">{cat}</div>', unsafe_allow_html=True)
                for faq in items:
                    with st.expander(f"❓ {faq['question']}"):
                        st.markdown(f'<div style="color:#222; line-height:1.7;">{faq["answer"]}</div>', unsafe_allow_html=True)
                        if st.button(f"🗑 Delete", key=f"del_faq_{faq['id']}"):
                            db.delete_faq(faq["id"])
                            st.rerun()

    with tab2:
        st.markdown('<div class="section-header">Add New FAQ</div>', unsafe_allow_html=True)
        with st.form("add_faq_form"):
            new_q = st.text_input("Question")
            new_a = st.text_area("Answer", height=120)
            new_cat = st.text_input("Category", value="General")
            submitted = st.form_submit_button("Add FAQ")
            if submitted:
                if new_q.strip() and new_a.strip():
                    db.insert_faq(new_q.strip(), new_a.strip(), new_cat.strip() or "General")
                    st.success("✅ FAQ added successfully.")
                    st.rerun()
                else:
                    st.error("Question and answer are required.")


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif nav == "📂 Admin":
    st.markdown("## Admin — Knowledge Management")
    st.markdown('<p style="color:#666; font-size:0.9rem;">Upload documents, manage the knowledge base, review flagged responses.</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Upload Documents", "Manage Documents", "QA Review"])

    # ── Upload ──────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="section-header">Upload New Document</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#777; font-size:0.85rem;">Supported formats: PDF, Word (.docx), Excel (.xlsx). Documents are chunked and indexed automatically.</p>', unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=["pdf", "docx", "xlsx"],
            label_visibility="collapsed",
        )

        if uploaded_files:
            if st.button("🚀 Ingest All Files"):
                progress = st.progress(0)
                results = []

                for i, uploaded_file in enumerate(uploaded_files):
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        try:
                            file_bytes = uploaded_file.read()
                            result = ingestion.ingest_file(file_bytes, uploaded_file.name)
                            results.append(("✅", uploaded_file.name, f"{result['chunks']} chunks indexed"))
                        except Exception as e:
                            results.append(("❌", uploaded_file.name, str(e)))
                    progress.progress((i + 1) / len(uploaded_files))

                progress.empty()
                for icon, name, msg in results:
                    if icon == "✅":
                        st.success(f"{icon} **{name}** — {msg}")
                    else:
                        st.error(f"{icon} **{name}** — {msg}")

                st.rerun()

    # ── Manage ──────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="section-header">Indexed Documents</div>', unsafe_allow_html=True)
        documents = db.get_all_documents()

        if not documents:
            st.info("No documents uploaded yet.")
        else:
            for doc in documents:
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.markdown(f'<div style="color:#1A1A1A; font-size:0.9rem; font-weight:500;">{doc["title"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="color:#555; font-size:0.75rem; font-family:\'IBM Plex Mono\',monospace;">{doc["source_file"]} · {doc["file_type"].upper()} · v{doc["version"]}</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div style="color:#777; font-size:0.8rem; padding-top:0.3rem;">{doc["created_at"][:10]}</div>', unsafe_allow_html=True)
                with col3:
                    if st.button("Delete", key=f"del_doc_{doc['id']}"):
                        db.delete_document(doc["id"])
                        st.warning(f"Deleted **{doc['title']}** (note: re-run the app to rebuild FAISS index)")
                        st.rerun()
                st.markdown('<hr style="margin:0.5rem 0;">', unsafe_allow_html=True)

    # ── QA Review ───────────────────────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="section-header">Flagged Responses (👎 Downvoted)</div>', unsafe_allow_html=True)
        all_feedback = db.get_all_feedback()
        negative = [f for f in all_feedback if f["rating"] == -1]

        if not negative:
            st.success("✅ No flagged responses — all good!")
        else:
            unreviewed = [f for f in negative if not f["reviewed"]]
            reviewed = [f for f in negative if f["reviewed"]]

            if unreviewed:
                st.markdown(f'<p style="color:#dc2626; font-size:0.85rem;">⚠️ {len(unreviewed)} unreviewed flagged response(s)</p>', unsafe_allow_html=True)
                for fb in unreviewed:
                    with st.expander(f"🔴 Query: \"{fb['query'][:60]}...\"  · {fb['timestamp'][:10]}"):
                        st.markdown(f'**Query:** {fb["query"]}')
                        st.markdown(f'**Response snippet:** {fb["result_snippet"]}')
                        if st.button("✅ Mark as Reviewed", key=f"review_{fb['id']}"):
                            db.mark_feedback_reviewed(fb["id"])
                            st.rerun()

            if reviewed:
                st.markdown(f'<p style="color:#777; font-size:0.8rem;">{len(reviewed)} previously reviewed</p>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif nav == "📊 Analytics":
    st.markdown("## Analytics")
    st.markdown('<p style="color:#666; font-size:0.9rem;">Search behaviour, knowledge gaps, and feedback insights.</p>', unsafe_allow_html=True)

    feedback_summary = db.get_feedback_summary()
    top_queries = db.get_top_queries(10)
    no_result_queries = db.get_no_result_queries(10)
    search_volume = db.get_search_volume_by_day(14)
    doc_count = len(db.get_all_documents())
    chunk_count = db.get_chunk_count()

    # ── Metric row ───────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, doc_count, "Documents"),
        (c2, chunk_count, "Chunks Indexed"),
        (c3, feedback_summary["total"], "Total Feedback"),
        (c4, feedback_summary["positive"], "👍 Positive"),
        (c5, feedback_summary["negative"], "👎 Flagged"),
    ]
    for col, val, label in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    # ── Top queries ──────────────────────────────────────────────────────────
    with col_left:
        st.markdown('<div class="section-header">Top Search Queries</div>', unsafe_allow_html=True)
        if not top_queries:
            st.markdown('<p style="color:#555; font-size:0.85rem;">No searches yet.</p>', unsafe_allow_html=True)
        else:
            max_count = max(q["count"] for q in top_queries)
            for q in top_queries:
                pct = int(q["count"] / max_count * 100)
                st.markdown(f"""
                <div style="margin-bottom:0.7rem;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                        <span style="color:#222; font-size:0.85rem;">{q['query'][:50]}</span>
                        <span style="font-family:'IBM Plex Mono',monospace; font-size:0.75rem; color:#777;">{q['count']}x</span>
                    </div>
                    <div style="background:#E8E3DA; border-radius:3px; height:4px;">
                        <div style="background:#E8C547; width:{pct}%; height:4px; border-radius:3px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Knowledge gaps ───────────────────────────────────────────────────────
    with col_right:
        st.markdown('<div class="section-header">Knowledge Gaps (Zero Results)</div>', unsafe_allow_html=True)
        if not no_result_queries:
            st.markdown('<p style="color:#16a34a; font-size:0.85rem;">✓ All queries returned results.</p>', unsafe_allow_html=True)
        else:
            for q in no_result_queries:
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding:0.5rem 0; border-bottom:1px solid #1e1e1e;">
                    <span style="color:#dc2626; font-size:0.85rem;">⚠ {q['query'][:50]}</span>
                    <span style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#666;">{q['count']}x</span>
                </div>
                """, unsafe_allow_html=True)

    # ── Search volume chart ──────────────────────────────────────────────────
    if search_volume:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Search Volume (Last 14 Days)</div>', unsafe_allow_html=True)

        import pandas as pd
        df = pd.DataFrame(search_volume)
        df.columns = ["Date", "Searches"]
        st.bar_chart(df.set_index("Date"), color="#E8C547", height=200)

    # ── Recent feedback ──────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Recent Feedback</div>', unsafe_allow_html=True)
    all_fb = db.get_all_feedback()
    if not all_fb:
        st.markdown('<p style="color:#555; font-size:0.85rem;">No feedback submitted yet.</p>', unsafe_allow_html=True)
    else:
        for fb in all_fb[:10]:
            icon = "👍" if fb["rating"] == 1 else "👎"
            color = "#16a34a" if fb["rating"] == 1 else "#dc2626"
            st.markdown(f"""
            <div style="display:flex; gap:1rem; padding:0.6rem 0; border-bottom:1px solid #1a1a1a; align-items:flex-start;">
                <span style="font-size:1rem; flex-shrink:0;">{icon}</span>
                <div style="flex:1;">
                    <div style="color:#222; font-size:0.85rem;">{fb['query'][:80]}</div>
                    <div style="color:#555; font-size:0.75rem; font-family:'IBM Plex Mono',monospace; margin-top:0.2rem;">{fb['timestamp'][:16]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
