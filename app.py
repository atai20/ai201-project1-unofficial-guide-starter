"""Gradio web UI for The Unofficial Guide."""

import gradio as gr

from query import ask
from store import CHROMA_DIR, build_vector_store


def ensure_index():
    if not CHROMA_DIR.exists():
        build_vector_store()


def handle_query(question: str):
    if not question.strip():
        return "Please enter a question.", ""
    result = ask(question.strip())
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources


ensure_index()

with gr.Blocks(title="The Unofficial Guide — UC Berkeley") as demo:
    gr.Markdown(
        """
# The Unofficial Guide
Ask questions about **UC Berkeley student life** — dining halls, housing, CS courses, and campus survival.
Answers are grounded in collected Reddit threads, Rate My Professors reviews, and student guides.
        """
    )
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. Is the housing lottery actually random?",
        lines=2,
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=10)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    examples = gr.Examples(
        examples=[
            ["What do students say about wait times at Crossroads during lunch?"],
            ["Which CS professor gives the most useful feedback?"],
            ["Is the Berkeley housing lottery completely random?"],
            ["What mold warnings exist for off-campus housing?"],
            ["What's the best dining hall according to students?"],
        ],
        inputs=inp,
    )

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

if __name__ == "__main__":
    demo.launch()
