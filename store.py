"""Embed chunks and store in ChromaDB."""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from chunk import chunk_documents
from ingest import load_documents

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "unofficial_guide"


def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def build_vector_store(persist_dir: Path | None = None, reset: bool = True) -> chromadb.Collection:
    """Load documents, chunk, embed, and persist to ChromaDB."""
    persist_dir = persist_dir or CHROMA_DIR

    documents = load_documents()
    chunks = chunk_documents(documents)

    if not chunks:
        raise ValueError("No chunks produced — check documents/ folder.")

    model = get_embedding_model()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    client = chromadb.PersistentClient(path=str(persist_dir))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"{c['source']}_{c['chunk_index']}" for c in chunks]
    metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]

    # Batch insert to avoid memory issues
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        collection.add(
            ids=ids[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            documents=texts[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    print(f"Indexed {len(chunks)} chunks from {len(documents)} documents.")
    return collection


def get_collection(persist_dir: Path | None = None) -> chromadb.Collection:
    """Load existing ChromaDB collection."""
    persist_dir = persist_dir or CHROMA_DIR
    client = chromadb.PersistentClient(path=str(persist_dir))
    return client.get_collection(COLLECTION_NAME)


if __name__ == "__main__":
    build_vector_store()
