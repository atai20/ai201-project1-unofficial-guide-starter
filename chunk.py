"""Split documents into overlapping chunks."""

CHUNK_SIZE = 450
CHUNK_OVERLAP = 80


def _split_at_boundaries(text: str, max_size: int) -> list[str]:
    """Split text preferring paragraph, then sentence, then hard breaks."""
    if len(text) <= max_size:
        return [text] if text.strip() else []

    parts: list[str] = []

    # Try paragraph split first
    paragraphs = text.split("\n\n")
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                parts.append(current)
            if len(para) <= max_size:
                current = para
            else:
                # Split long paragraph by sentences
                sentences = re_split_sentences(para)
                current = ""
                for sent in sentences:
                    candidate = f"{current} {sent}".strip() if current else sent
                    if len(candidate) <= max_size:
                        current = candidate
                    else:
                        if current:
                            parts.append(current)
                        if len(sent) <= max_size:
                            current = sent
                        else:
                            # Hard split as last resort
                            for i in range(0, len(sent), max_size):
                                parts.append(sent[i : i + max_size])
                            current = ""
    if current.strip():
        parts.append(current.strip())

    return parts


def re_split_sentences(text: str) -> list[str]:
    """Split on sentence boundaries."""
    import re

    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split a single document into overlapping chunks."""
    base_chunks = _split_at_boundaries(text, chunk_size)
    if not base_chunks:
        return []

    if overlap <= 0 or len(base_chunks) == 1:
        return base_chunks

    overlapped: list[str] = []
    for i, chunk in enumerate(base_chunks):
        if i == 0:
            overlapped.append(chunk)
        else:
            prev = base_chunks[i - 1]
            prefix = prev[-overlap:] if len(prev) >= overlap else prev
            merged = f"{prefix} {chunk}".strip()
            overlapped.append(merged)

    return overlapped


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk all documents.

    Returns list of dicts: source, chunk_index, text.
    """
    all_chunks: list[dict] = []
    for doc in documents:
        chunks = chunk_text(doc["text"])
        for idx, chunk in enumerate(chunks):
            if chunk.strip():
                all_chunks.append(
                    {
                        "source": doc["source"],
                        "chunk_index": idx,
                        "text": chunk.strip(),
                    }
                )
    return all_chunks


if __name__ == "__main__":
    from ingest import load_documents

    docs = load_documents()
    chunks = chunk_documents(docs)
    print(f"Total chunks: {len(chunks)}")
    print("\n--- 5 sample chunks ---")
    for i, c in enumerate(chunks[:5]):
        print(f"\n[{i + 1}] Source: {c['source']} (chunk {c['chunk_index']})")
        print(c["text"][:300] + ("..." if len(c["text"]) > 300 else ""))
