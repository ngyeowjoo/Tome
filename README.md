# 📚 Tome — AI Knowledge Base

An AI-powered knowledge assistant for call center agents. Search across FAQs, SOPs, and uploaded documents. Powered by Claude (Anthropic) and sentence-transformers.

---

## ✨ Features

- **Hybrid Search** — keyword + semantic (FAISS) retrieval
- **AI Answers** — Claude generates context-aware answers with confidence scoring
- **Multi-format Ingestion** — PDF, Word (.docx), Excel (.xlsx)
- **FAQ Management** — structured Q&A browsable by category
- **Feedback Loop** — 👍/👎 ratings, QA review queue for flagged responses
- **Analytics** — top queries, knowledge gaps, search volume, feedback trends

---

## 🚀 Deploy on Streamlit Cloud

### 1. Fork / Clone this repository

```bash
git clone https://github.com/YOUR_USERNAME/tome.git
cd tome
```

### 2. Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 3. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Select your repository, branch `main`, entrypoint `app.py`
4. Under **Advanced settings → Secrets**, paste:

```toml
ANTHROPIC_API_KEY = "sk-ant-your-actual-key"
```

5. Click **Deploy**

---

## 💻 Run Locally

```bash
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:
```toml
ANTHROPIC_API_KEY = "sk-ant-your-actual-key"
```

```bash
streamlit run app.py
```

---

## 🗂 Project Structure

```
app.py                      # Main Streamlit app
modules/
    db.py                   # SQLite layer (all reads/writes)
    ingestion.py            # File parsing, chunking, FAISS embedding
    ai.py                   # Claude answer generation
data/
    tome.db                 # SQLite database (auto-created)
    faiss_index/            # FAISS vector index (auto-created)
    documents/              # Placeholder
.streamlit/
    config.toml             # Theme config
    secrets.toml            # API keys (DO NOT COMMIT)
requirements.txt
```

---

## ⚙️ Tech Stack

| Layer        | Technology                         |
|--------------|------------------------------------|
| Frontend     | Streamlit                          |
| AI           | Anthropic Claude (claude-sonnet)   |
| Embeddings   | sentence-transformers (MiniLM-L6)  |
| Vector Store | FAISS (CPU)                        |
| Database     | SQLite                             |
| Hosting      | Streamlit Cloud                    |

---

## ⚠️ Notes

- **No authentication** — designed for internal/trusted teams
- FAISS index is rebuilt from SQLite on first load if index file is missing
- Streamlit Cloud uses ephemeral storage — for persistence across restarts, consider upgrading to a managed DB (Supabase, PlanetScale) in v2
- Deleting a document from Admin removes it from SQLite but requires app restart to reflect in FAISS

---

## 🔮 Roadmap (Post-MVP)

- [ ] Authentication (Streamlit-Authenticator or RBAC)
- [ ] Persistent cloud storage (Supabase / S3)
- [ ] Auto FAQ generation from top queries
- [ ] Real-time agent assist integration
- [ ] Ranking optimization via feedback signals
