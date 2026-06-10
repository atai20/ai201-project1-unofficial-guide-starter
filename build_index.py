"""Build the vector index from documents."""

from store import build_vector_store

if __name__ == "__main__":
    build_vector_store(reset=True)
