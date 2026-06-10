"""Semantic retrieval from ChromaDB."""

from pathlib import Path

from sentence_transformers import SentenceTransformer

from store import COLLECTION_NAME, EMBEDDING_MODEL, CHROMA_DIR, get_collection

TOP_K = 5

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def retrieve(
    query: str,
    top_k: int = TOP_K,
    persist_dir: Path | None = None,
) -> list[dict]:
    """
    Retrieve top-k relevant chunks for a query.

    Returns list of dicts: text, source, chunk_index, distance.
    """
    collection = get_collection(persist_dir)
    model = _get_model()
    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    if not results["documents"] or not results["documents"][0]:
        return chunks

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            {
                "text": doc,
                "source": meta["source"],
                "chunk_index": meta["chunk_index"],
                "distance": dist,
            }
        )
    return chunks


if __name__ == "__main__":
    import sys

    from store import build_vector_store

    if not CHROMA_DIR.exists():
        build_vector_store()

    test_queries = [
        "What do students say about wait times at Crossroads during lunch?",
        "Which CS professor gives the most useful feedback?",
        "Is the housing lottery completely random?",
    ]

    queries = sys.argv[1:] if len(sys.argv) > 1 else test_queries

    for q in queries:
        print(f"\n{'=' * 60}\nQuery: {q}\n{'=' * 60}")
        results = retrieve(q)
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] distance={r['distance']:.4f} | {r['source']} (chunk {r['chunk_index']})")
            print(r["text"][:250] + ("..." if len(r["text"]) > 250 else ""))
