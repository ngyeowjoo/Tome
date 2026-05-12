"""
app.py — Tome: AI Knowledge Base for Call Center Agents
"""

import streamlit as st
import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))
import db, ingestion, ai, search

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
</style>
""", unsafe_allow_html=True)

# ── Init DB ────────────────────────────────────────────────────────────────────

db.init_db()
search.init_synonym_table()

# ── Session state ──────────────────────────────────────────────────────────────

if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = False
if "ai_mode" not in st.session_state:
    st.session_state.ai_mode = False
if "corrected_query" not in st.session_state:
    st.session_state.corrected_query = None

# Pre-fill from URL query param (Chrome extension)
_params = st.query_params
if "q" in _params and not st.session_state.last_query:
    st.session_state.last_query = _params["q"]

# ── Helper functions ───────────────────────────────────────────────────────────

def _run_search(query):
    expanded = search.expand_query_with_synonyms(query)
    chunks = ingestion.hybrid_search(expanded, top_k=8)
    chunks = search.rerank_chunks(query, chunks)[:5]
    faqs = db.get_all_faqs()
    matched_faqs = search.enhanced_faq_match(query, faqs)
    return {"chunks": chunks, "matched_faqs": matched_faqs, "mode": "search", "expanded_query": expanded}

def _run_ai(query):
    expanded = search.expand_query_with_synonyms(query)
    chunks = ingestion.hybrid_search(expanded, top_k=8)
    chunks = search.rerank_chunks(query, chunks)[:5]
    result = ai.generate_answer(query, chunks)
    result["chunks"] = chunks
    faqs = db.get_all_faqs()
    result["matched_faqs"] = search.enhanced_faq_match(query, faqs)
    result["mode"] = "ai"
    result["expanded_query"] = expanded
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
    cleaned = [l.strip() for l in answer_lines if l.strip() and not l.strip().startswith('#')]
    return question, '\n'.join(cleaned)

def _highlight(text, query):
    """Delegate to search.highlight_text for phrase + word highlighting."""
    return search.highlight_text(text, query)

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
                bullets.append(f'<div style="margin-bottom:0.4rem;">• {part}</div>')
    return "\n".join(bullets)

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="tome-logo">📚 Tome</div>', unsafe_allow_html=True)
    st.markdown('<div class="tome-sub">Knowledge Base</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    nav = st.radio(
        "Navigation",
        ["🔍 Search", "📋 FAQs", "📂 Admin", "📊 Analytics"],
        label_visibility="collapsed",
        key="main_nav",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">System Status</div>', unsafe_allow_html=True)

    chunk_count = db.get_chunk_count()
    doc_count = len(db.get_all_documents())
    faq_count = len(db.get_all_faqs())

    st.markdown(f"""
    <div style="font-family:monospace; font-size:0.75rem; color:#888; line-height:2;">
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
        st.markdown('<p style="font-family:monospace; font-size:0.7rem; color:#C4992A;">⚡ AI mode — uses Anthropic API</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="font-family:monospace; font-size:0.7rem; color:#16a34a;">✓ Search mode — no API needed</p>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH PAGE
# ═══════════════════════════════════════════════════════════════════════════════

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
            placeholder="e.g. I have forgotten my CPF Investment Account Number.",
            label_visibility="collapsed",
            key="search_input",
            value=st.session_state.last_query,
        )
    with col2:
        search_clicked = st.button("Search →", use_container_width=True)

    if (query and query != st.session_state.last_query) or (search_clicked and query):
        st.session_state.feedback_given = False
        st.session_state.last_query = query
        st.session_state.last_result = None
        msg = "Searching + generating answer..." if st.session_state.ai_mode else "Searching knowledge base..."
        with st.spinner(msg):
            try:
                # Typo correction
                all_chunks_for_typo = db.get_all_chunks()
                all_faqs_for_typo = db.get_all_faqs()
                corrected_query, was_corrected = search.correct_query_typos(query, all_faqs_for_typo, all_chunks_for_typo)
                if was_corrected:
                    st.session_state.corrected_query = corrected_query
                else:
                    st.session_state.corrected_query = None

                result = _run_ai(corrected_query) if st.session_state.ai_mode else _run_search(corrected_query)
                db.log_search(query, len(result.get("chunks", [])))
                st.session_state.last_result = result
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.last_result = None

    if not st.session_state.last_query:
        st.markdown("<br>" * 3, unsafe_allow_html=True)
        icon = "🤖" if st.session_state.ai_mode else "🔍"
        label = "Ask a question to generate an AI answer" if st.session_state.ai_mode else "Start typing to search the knowledge base"
        st.markdown(f"""
        <div style="text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">{icon}</div>
            <div style="font-family:monospace; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.15em; color:#888;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    elif st.session_state.last_result:
        result = st.session_state.last_result
        chunks = result.get("chunks", [])

        # Typo correction notice
        if st.session_state.get("corrected_query"):
            st.info(f"🔤 Showing results for **{st.session_state.corrected_query}** (auto-corrected)")

        # Synonym expansion notice
        expanded = result.get("expanded_query", "")
        if expanded and expanded.strip() != st.session_state.last_query.strip():
            extra = expanded.replace(st.session_state.last_query, "").strip()
            if extra:
                st.caption(f"🔗 Query expanded with synonyms: _{extra}_")

        # AI answer
        if result.get("mode") == "ai":
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">AI Answer</div>', unsafe_allow_html=True)
            conf_label = result.get("confidence_label", "MEDIUM")
            conf_class = f"conf-{conf_label.lower()}"
            conf_score = int(result.get("confidence", 0.5) * 100)
            st.markdown(f"""
            <div class="answer-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.8rem;">
                    <span style="font-family:monospace; font-size:0.7rem; color:#555; text-transform:uppercase; letter-spacing:0.1em;">Generated by Claude</span>
                    <span class="{conf_class}" style="font-family:monospace; font-size:0.75rem;">◆ {conf_label} CONFIDENCE ({conf_score}%)</span>
                </div>
                <div style="color:#1A1A1A; line-height:1.7; font-size:0.95rem;">{_highlight(result['answer'], st.session_state.last_query).replace(chr(10), '<br>')}</div>
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

        # Results
        if chunks:
            st.markdown("<br>", unsafe_allow_html=True)
            header = "Top Results" if result.get("mode") == "search" else "Supporting Sources"
            st.markdown(f'<div class="section-header">{header}</div>', unsafe_allow_html=True)

            if result.get("mode") == "search":
                for chunk in chunks:
                    src_badge = '<span class="tag">semantic</span>' if chunk.get("source") == "semantic" else '<span class="tag">keyword</span>'
                    score_pct = int(chunk.get("score", 0) * 100)
                    question, answer = _extract_qa(chunk["content"])
                    title = question if question else chunk.get("title", "Result")
                    score_pct = chunk.get("score_pct", score_pct)
                    explanation = chunk.get("score_explanation", "Semantic similarity")
                    match_color = chunk.get("match_color", "#555")
                    highlighted_title = _highlight(title, st.session_state.last_query)
                    with st.expander(f"❓ {title}  —  {score_pct}% match"):
                        st.markdown(f'<div style="font-size:0.95rem;font-weight:600;margin-bottom:0.5rem;">❓ {highlighted_title}</div>', unsafe_allow_html=True)
                        st.markdown(
                            f'{src_badge} <span style="font-family:monospace;font-size:0.72rem;color:{match_color};font-weight:600;">{score_pct}% — {explanation}</span>',
                            unsafe_allow_html=True
                        )
                        st.markdown("")
                        text_to_display = answer if answer else chunk["content"]
                        highlighted = _highlight(text_to_display, st.session_state.last_query)
                        bullets = _format_answer_bullets(highlighted)
                        st.markdown(bullets, unsafe_allow_html=True)
                        st.markdown(f'<p style="font-size:0.75rem; color:#999; margin-top:1rem; border-top:1px solid #eee; padding-top:0.5rem;">📄 Source: <strong>{chunk.get("title", "Document")}</strong></p>', unsafe_allow_html=True)
            else:
                for chunk in chunks[:4]:
                    src_badge = '<span class="tag">semantic</span>' if chunk.get("source") == "semantic" else '<span class="tag">keyword</span>'
                    score_pct = int(chunk.get("score", 0) * 100)
                    question, answer = _extract_qa(chunk["content"])
                    title = question if question else chunk.get("title", "Result")
                    with st.expander(f"📄 {title}  —  {score_pct}% match"):
                        st.markdown(src_badge, unsafe_allow_html=True)
                        st.write(answer if answer else chunk["content"])
        else:
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

# ═══════════════════════════════════════════════════════════════════════════════
# FAQs PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif nav == "📋 FAQs":
    st.markdown("## Frequently Asked Questions")
    tab1, tab2 = st.tabs(["Browse FAQs", "Add FAQ"])

    with tab1:
        faqs = db.get_all_faqs()
        if not faqs:
            st.info("No FAQs yet. Add some in the 'Add FAQ' tab.")
        else:
            categories = {}
            for faq in faqs:
                cat = faq.get("category", "General")
                categories.setdefault(cat, []).append(faq)
            for cat, items in categories.items():
                st.markdown(f'<div class="section-header">{cat}</div>', unsafe_allow_html=True)
                for faq in items:
                    q = st.session_state.get("last_query", "")
                    hl_question = _highlight(faq["question"], q) if q else faq["question"]
                    hl_answer = _highlight(faq["answer"], q) if q else faq["answer"]
                    with st.expander(f"❓ {faq['question']}"):
                        st.markdown(f'<div style="font-weight:600;margin-bottom:0.4rem;">❓ {hl_question}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div style="color:#555;line-height:1.7;">{hl_answer}</div>', unsafe_allow_html=True)
                        if st.button("🗑 Delete", key=f"del_faq_{faq['id']}"):
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

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Upload Documents", "Manage Documents", "QA Review", "View Chunks", "Synonyms"])

    with tab1:
        st.markdown('<div class="section-header">Upload New Document</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#888; font-size:0.85rem;">Supported: PDF, Word (.docx), Excel (.xlsx), Markdown (.md).</p>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=["pdf", "docx", "xlsx", "md"],
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

    with tab2:
        st.markdown('<div class="section-header">Indexed Documents</div>', unsafe_allow_html=True)
        documents = db.get_all_documents()
        if not documents:
            st.info("No documents uploaded yet.")
        else:
            for doc in documents:
                c1, c2, c3 = st.columns([4, 2, 1])
                with c1:
                    st.markdown(f'<div style="color:#1A1A1A; font-weight:500;">{doc["title"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="color:#888; font-size:0.75rem; font-family:monospace;">{doc["source_file"]} · {doc["file_type"].upper()}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div style="color:#888; font-size:0.8rem;">{doc["created_at"][:10]}</div>', unsafe_allow_html=True)
                with c3:
                    if st.button("Delete", key=f"del_doc_{doc['id']}"):
                        db.delete_document(doc["id"])
                        st.rerun()
                st.markdown('<hr style="margin:0.5rem 0;">', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="section-header">Flagged Responses (👎 Downvoted)</div>', unsafe_allow_html=True)
        all_feedback = db.get_all_feedback()
        negative = [f for f in all_feedback if f["rating"] == -1]
        if not negative:
            st.success("✅ No flagged responses.")
        else:
            unreviewed = [f for f in negative if not f["reviewed"]]
            if unreviewed:
                st.markdown(f'<p style="color:#dc2626; font-size:0.85rem;">⚠️ {len(unreviewed)} unreviewed</p>', unsafe_allow_html=True)
                for fb in unreviewed:
                    with st.expander(f"🔴 {fb['query'][:60]} · {fb['timestamp'][:10]}"):
                        st.write(f"**Query:** {fb['query']}")
                        st.write(f"**Snippet:** {fb['result_snippet']}")
                        if st.button("✅ Mark Reviewed", key=f"review_{fb['id']}"):
                            db.mark_feedback_reviewed(fb["id"])
                            st.rerun()

    with tab4:
        st.markdown('<div class="section-header">Indexed Chunks</div>', unsafe_allow_html=True)
        documents = db.get_all_documents()
        if not documents:
            st.info("No documents indexed yet.")
        else:
            doc_options = {f"{d['title']} ({d['source_file']})": d['id'] for d in documents}
            selected = st.selectbox("Filter by document", ["All documents"] + list(doc_options.keys()), label_visibility="collapsed")
            chunk_search = st.text_input("Search within chunks", placeholder="Filter by keyword...", label_visibility="collapsed")
            all_chunks = db.get_all_chunks()
            if selected != "All documents":
                doc_id = doc_options[selected]
                all_chunks = [c for c in all_chunks if c.get("document_id") == doc_id]
            if chunk_search.strip():
                all_chunks = [c for c in all_chunks if chunk_search.lower() in c["content"].lower()]
            st.markdown(f'<p style="font-family:monospace; font-size:0.75rem; color:#888;">{len(all_chunks)} chunk(s)</p>', unsafe_allow_html=True)
            for chunk in all_chunks:
                label = f"#{chunk.get('chunk_index',0)+1} · {chunk['title']} · {len(chunk['content'].split())} words"
                with st.expander(label):
                    st.write(chunk["content"])

    with tab5:
        st.markdown('<div class="section-header">Synonym Groups</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#777; font-size:0.85rem;">Define synonyms to expand search queries. e.g. "CPF" → "retirement fund, provident fund". Agents can use any term and the system will search for all.</p>', unsafe_allow_html=True)

        # Add new group
        with st.form("add_synonym_form"):
            st.markdown("**Add Synonym Group**")
            col_a, col_b = st.columns([1, 2])
            with col_a:
                canonical = st.text_input("Main term", placeholder="e.g. cpf")
            with col_b:
                variants_input = st.text_input("Synonyms (comma-separated)", placeholder="e.g. retirement fund, provident fund, cpf savings")
            if st.form_submit_button("Add Group"):
                if canonical.strip() and variants_input.strip():
                    variants = [v.strip() for v in variants_input.split(",") if v.strip()]
                    search.add_synonym_group(canonical, variants)
                    st.success(f"✅ Added: **{canonical}** → {variants}")
                    st.rerun()
                else:
                    st.error("Both fields are required.")

        st.markdown("<br>", unsafe_allow_html=True)
        groups = search.get_all_synonym_groups()
        if not groups:
            st.info("No synonym groups yet. Add one above.")
        else:
            st.markdown('<div class="section-header">Existing Groups</div>', unsafe_allow_html=True)
            for group in groups:
                col1, col2 = st.columns([5, 1])
                with col1:
                    variants = str(group.get("variants", ""))
                    st.markdown(f'<div style="padding:0.6rem 0; border-bottom:1px solid #eee;"><strong style="color:#C4992A;">{group["canonical"]}</strong> → <span style="color:#555;">{variants}</span></div>', unsafe_allow_html=True)
                with col2:
                    if st.button("Delete", key=f"del_syn_{group['id']}"):
                        search.delete_synonym_group(group["id"])
                        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif nav == "📊 Analytics":
    st.markdown("## Analytics")

    feedback_summary = db.get_feedback_summary()
    top_queries = db.get_top_queries(10)
    no_result_queries = db.get_no_result_queries(10)
    search_volume = db.get_search_volume_by_day(14)

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, label in [
        (c1, len(db.get_all_documents()), "Documents"),
        (c2, db.get_chunk_count(), "Chunks"),
        (c3, feedback_summary["total"], "Feedback"),
        (c4, feedback_summary["positive"], "👍 Positive"),
        (c5, feedback_summary["negative"], "👎 Flagged"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="section-header">Top Search Queries</div>', unsafe_allow_html=True)
        if not top_queries:
            st.write("No searches yet.")
        else:
            max_count = max(q["count"] for q in top_queries)
            for q in top_queries:
                pct = int(q["count"] / max_count * 100)
                st.markdown(f"""
                <div style="margin-bottom:0.7rem;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                        <span style="color:#333; font-size:0.85rem;">{q['query'][:50]}</span>
                        <span style="font-family:monospace; font-size:0.75rem; color:#888;">{q['count']}x</span>
                    </div>
                    <div style="background:#E8E3DA; border-radius:3px; height:4px;">
                        <div style="background:#C4992A; width:{pct}%; height:4px; border-radius:3px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="section-header">Knowledge Gaps (Zero Results)</div>', unsafe_allow_html=True)
        if not no_result_queries:
            st.markdown('<p style="color:#16a34a;">✓ All queries returned results.</p>', unsafe_allow_html=True)
        else:
            for q in no_result_queries:
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:0.5rem 0; border-bottom:1px solid #eee;">
                    <span style="color:#dc2626; font-size:0.85rem;">⚠ {q['query'][:50]}</span>
                    <span style="font-family:monospace; font-size:0.7rem; color:#888;">{q['count']}x</span>
                </div>
                """, unsafe_allow_html=True)

    if search_volume:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Search Volume (Last 14 Days)</div>', unsafe_allow_html=True)
        import pandas as pd
        df = pd.DataFrame(search_volume)
        df.columns = ["Date", "Searches"]
        st.bar_chart(df.set_index("Date"), color="#C4992A", height=200)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Recent Feedback</div>', unsafe_allow_html=True)
    all_fb = db.get_all_feedback()
    if not all_fb:
        st.write("No feedback yet.")
    else:
        for fb in all_fb[:10]:
            icon = "👍" if fb["rating"] == 1 else "👎"
            st.markdown(f"""
            <div style="display:flex; gap:1rem; padding:0.6rem 0; border-bottom:1px solid #eee;">
                <span>{icon}</span>
                <div>
                    <div style="color:#333; font-size:0.85rem;">{fb['query'][:80]}</div>
                    <div style="color:#888; font-size:0.75rem; font-family:monospace;">{fb['timestamp'][:16]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
