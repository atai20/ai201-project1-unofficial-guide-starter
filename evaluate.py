"""Run evaluation plan questions and print results."""

import json
from pathlib import Path

from query import ask
from retrieve import retrieve
from store import CHROMA_DIR, build_vector_store

EVAL_QUESTIONS = [
    {
        "id": 1,
        "question": "What do students say about wait times at Crossroads during lunch?",
        "expected": "Lunch rush 12–1:30 pm brings 20–25 minute waits for hot food; shorter lines before noon, after 2 pm, or at the salad bar.",
    },
    {
        "id": 2,
        "question": "Which CS professor gives the most useful feedback according to reviews?",
        "expected": "Josh Hug (CS 61B) — reviewers praise detailed autograder feedback, written style comments, and accessible office hours.",
    },
    {
        "id": 3,
        "question": "Is the Berkeley housing lottery completely random?",
        "expected": "No — lottery numbers are random within class year, but re-applicants get priority over new applicants; disabled students and athletes have separate processes.",
    },
    {
        "id": 4,
        "question": "What mold-related warning do students give about off-campus housing?",
        "expected": "Several units in the Dwight-Telegraph corridor have mold complaints; students advise asking about ventilation, checking for musty smells during tours, and documenting move-in conditions.",
    },
    {
        "id": 5,
        "question": "How long does the CS 162 Pintos project take according to reviews?",
        "expected": "40+ hours; students recommend starting project 2 the day it is released.",
    },
]


def run_evaluation():
    if not CHROMA_DIR.exists():
        build_vector_store()

    results = []
    for item in EVAL_QUESTIONS:
        q = item["question"]
        chunks = retrieve(q)
        result = ask(q)
        entry = {
            "id": item["id"],
            "question": q,
            "expected": item["expected"],
            "answer": result["answer"],
            "sources": result["sources"],
            "top_chunks": [
                {
                    "source": c["source"],
                    "distance": c["distance"],
                    "text": c["text"][:200],
                }
                for c in chunks[:3]
            ],
        }
        results.append(entry)
        print(f"\n{'=' * 70}")
        print(f"Q{item['id']}: {q}")
        print(f"Expected: {item['expected']}")
        print(f"Answer: {result['answer'][:500]}")
        print(f"Sources: {result['sources']}")
        for i, c in enumerate(chunks[:2], 1):
            print(f"  Chunk {i}: {c['source']} (dist={c['distance']:.4f})")

    out_path = Path(__file__).parent / "evaluation_results.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved results to evaluation_results.json")
    return results


if __name__ == "__main__":
    run_evaluation()
