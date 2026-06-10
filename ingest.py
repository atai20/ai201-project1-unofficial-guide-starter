"""Load and clean documents from the documents/ folder."""

import re
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).parent / "documents"

# Patterns to strip from scraped/copied forum text
BOILERPLATE_PATTERNS = [
    r"^Source:.*$",
    r"^Thread collected.*$",
    r"^Topic:.*$",
    r"^Title:.*$",
    r"^Course:.*$",
    r"^Primary instructor.*$",
    r"^Instructors:.*$",
]


def clean_text(text: str) -> str:
    """Remove boilerplate headers and normalize whitespace."""
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        skip = False
        for pattern in BOILERPLATE_PATTERNS:
            if re.match(pattern, stripped, re.IGNORECASE):
                skip = True
                break
        if skip:
            continue
        # Remove HTML entities if any slipped in
        stripped = stripped.replace("&amp;", "&").replace("&#39;", "'").replace("&nbsp;", " ")
        cleaned_lines.append(stripped)

    text = "\n".join(cleaned_lines)
    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_documents(documents_dir: Path | None = None) -> list[dict]:
    """
    Load all .txt documents from documents_dir.

    Returns list of dicts with keys: source (filename), text (cleaned content).
    """
    documents_dir = documents_dir or DOCUMENTS_DIR
    documents = []

    for path in sorted(documents_dir.glob("*.txt")):
        raw = path.read_text(encoding="utf-8")
        cleaned = clean_text(raw)
        if cleaned:
            documents.append({"source": path.name, "text": cleaned})

    return documents


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")
    if docs:
        print(f"\n--- Sample from {docs[0]['source']} ---")
        print(docs[0]["text"][:500])
