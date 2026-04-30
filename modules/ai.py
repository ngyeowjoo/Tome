"""
modules/ai.py — Claude-powered answer generation for Tome
"""

import streamlit as st
import anthropic


def _get_client() -> anthropic.Anthropic:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in Streamlit secrets.")
    return anthropic.Anthropic(api_key=api_key)


def generate_answer(query: str, context_chunks: list[dict]) -> dict:
    """
    Generate a Claude answer given a query and retrieved context chunks.
    Returns dict with: answer, confidence, sources.
    """
    if not context_chunks:
        return {
            "answer": "I couldn't find relevant information in the knowledge base to answer this question. Try rephrasing or check if the relevant documents have been uploaded.",
            "confidence": 0.0,
            "sources": [],
        }

    # Build context block
    context_parts = []
    for i, chunk in enumerate(context_chunks[:5]):
        source = chunk.get("title", "Unknown")
        context_parts.append(f"[Source {i+1}: {source}]\n{chunk['content']}")

    context_text = "\n\n---\n\n".join(context_parts)

    system_prompt = """You are Tome, an intelligent knowledge assistant for a call center team.
Your role is to provide accurate, concise, and helpful answers based strictly on the provided knowledge base content.

Guidelines:
- Answer directly and confidently when the context supports it
- Be specific — reference exact steps, policies, or procedures when relevant
- If the context is insufficient, say so clearly rather than guessing
- Use plain language appropriate for call center agents
- Format with bullet points or numbered steps when listing procedures
- Keep answers focused — agents need quick, actionable information
- At the end, provide a confidence level: HIGH, MEDIUM, or LOW based on how well the context answers the question"""

    user_message = f"""Question: {query}

Knowledge Base Context:
{context_text}

Please answer the question based on the context above. End your response with:
CONFIDENCE: [HIGH/MEDIUM/LOW]"""

    client = _get_client()
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_answer = message.content[0].text.strip()

    # Parse confidence from end of response
    confidence_map = {"HIGH": 0.9, "MEDIUM": 0.6, "LOW": 0.3}
    confidence_score = 0.5
    clean_answer = raw_answer

    for level, score in confidence_map.items():
        marker = f"CONFIDENCE: {level}"
        if marker in raw_answer:
            confidence_score = score
            clean_answer = raw_answer.replace(marker, "").strip().rstrip("—-").strip()
            break

    sources = [
        {"title": c.get("title", "Unknown"), "snippet": c["content"][:200] + "..."}
        for c in context_chunks[:3]
    ]

    return {
        "answer": clean_answer,
        "confidence": confidence_score,
        "confidence_label": _confidence_label(confidence_score),
        "sources": sources,
    }


def _confidence_label(score: float) -> str:
    if score >= 0.8:
        return "HIGH"
    elif score >= 0.5:
        return "MEDIUM"
    else:
        return "LOW"


def search_faqs(query: str, faqs: list[dict]) -> list[dict]:
    """
    Use Claude to match a query against FAQ list and return best matches.
    Returns up to 3 relevant FAQs.
    """
    if not faqs:
        return []

    faq_list = "\n".join(
        f"{i+1}. Q: {f['question']}\n   A: {f['answer']}"
        for i, f in enumerate(faqs[:50])
    )

    client = _get_client()
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"""Given this user query: "{query}"

Review these FAQs and return the numbers of the top 3 most relevant ones (comma-separated), or "none" if none are relevant.
Only return the numbers, nothing else.

FAQs:
{faq_list}"""
        }],
    )

    response = message.content[0].text.strip().lower()
    if response == "none":
        return []

    try:
        indices = [int(x.strip()) - 1 for x in response.split(",") if x.strip().isdigit()]
        return [faqs[i] for i in indices if 0 <= i < len(faqs)]
    except Exception:
        return []
