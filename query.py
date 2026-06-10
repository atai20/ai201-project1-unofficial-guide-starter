"""End-to-end grounded question answering."""

import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are The Unofficial Guide, a campus knowledge assistant for UC Berkeley students.

STRICT RULES:
1. Answer ONLY using the provided document excerpts. Do not use outside knowledge.
2. If the excerpts do not contain enough information, respond exactly: "I don't have enough information on that in my documents."
3. Be specific and cite which source document(s) support your answer inline, e.g. (source: reddit_foothill_dining.txt).
4. Do not invent facts, statistics, or professor names not present in the excerpts.
5. Keep answers concise (2-4 sentences unless the question requires a list)."""


def _format_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[Excerpt {i} | source: {c['source']} | chunk {c['chunk_index']}]\n{c['text']}"
        )
    return "\n\n".join(parts)


def ask(question: str, top_k: int = 5) -> dict:
    """
    Retrieve context and generate a grounded answer.

    Returns dict with keys: answer, sources (list of source filenames), chunks (retrieved).
    """
    chunks = retrieve(question, top_k=top_k)
    sources = list(dict.fromkeys(c["source"] for c in chunks))

    if not chunks:
        return {
            "answer": "I don't have enough information on that in my documents.",
            "sources": [],
            "chunks": [],
        }

    context = _format_context(chunks)
    user_message = f"""Document excerpts:
{context}

Question: {question}

Answer using ONLY the excerpts above. Cite source filenames in your response."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_key_here":
        # Fallback for testing without API key
        return {
            "answer": (
                "[GROQ_API_KEY not set — retrieval-only mode]\n\n"
                f"Top retrieved excerpt from {chunks[0]['source']}:\n{chunks[0]['text'][:400]}"
            ),
            "sources": sources,
            "chunks": chunks,
        }

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
        max_tokens=512,
    )

    answer = response.choices[0].message.content.strip()

    # Programmatic source attribution appended
    source_line = "Retrieved from: " + ", ".join(sources)
    if not any(s in answer for s in sources):
        answer = f"{answer}\n\n{source_line}"

    return {"answer": answer, "sources": sources, "chunks": chunks}


if __name__ == "__main__":
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "What do students say about Foothill dining?"
    result = ask(q)
    print("Answer:", result["answer"])
    print("\nSources:", result["sources"])
