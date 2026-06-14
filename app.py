"""
EMU Unofficial Housing Guide — Gradio web interface.

Run:
    .venv/bin/python app.py
Then open http://localhost:7860
"""

import gradio as gr
from generate import ask

EXAMPLE_QUESTIONS = [
    "What do residents say about BEAL properties?",
    "What do residents say about the Depot Town area?",
    "Would past residents recommend living at Lakeshore?",
    "Is the community around Lakeshore walkable?",
    "Should a student rent at Aspen Chase or Chestnut Lake?",
]

CSS = """
/* ── page background ── */
body, .gradio-container {
    background: #0f1117 !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}

/* ── header card ── */
#header {
    background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
    border: 1px solid #2a3450;
    border-radius: 16px;
    padding: 32px 40px 24px;
    margin-bottom: 24px;
    text-align: center;
}
#header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #e8eaf0;
    margin: 0 0 8px;
    letter-spacing: -0.5px;
}
#header p {
    color: #7a8aaa;
    font-size: 0.95rem;
    margin: 0;
}

/* ── input card ── */
#input-card {
    background: #1a1f2e;
    border: 1px solid #2a3450;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
}

/* ── textboxes ── */
textarea, input[type="text"] {
    background: #0f1117 !important;
    border: 1px solid #2a3450 !important;
    border-radius: 10px !important;
    color: #e8eaf0 !important;
    font-size: 0.95rem !important;
    padding: 12px 14px !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #4f6ef7 !important;
    box-shadow: 0 0 0 3px rgba(79,110,247,0.18) !important;
}
label span {
    color: #7a8aaa !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ── primary ask button ── */
#ask-btn {
    background: linear-gradient(135deg, #4f6ef7, #7c4dff) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    height: 44px !important;
    transition: opacity 0.15s, transform 0.1s !important;
}
#ask-btn:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

/* ── example pill buttons ── */
.example-btn button {
    background: #1e2538 !important;
    border: 1px solid #2a3450 !important;
    border-radius: 20px !important;
    color: #a0aec0 !important;
    font-size: 0.78rem !important;
    padding: 5px 12px !important;
    transition: background 0.15s, color 0.15s !important;
    white-space: normal !important;
    text-align: left !important;
    height: auto !important;
    line-height: 1.4 !important;
}
.example-btn button:hover {
    background: #2a3450 !important;
    color: #e8eaf0 !important;
    border-color: #4f6ef7 !important;
}

/* ── output cards ── */
#answer-card, #sources-card {
    background: #1a1f2e;
    border: 1px solid #2a3450;
    border-radius: 14px;
    padding: 24px;
}
#answer-card textarea {
    border: none !important;
    background: transparent !important;
    color: #d4daf0 !important;
    font-size: 0.95rem !important;
    line-height: 1.7 !important;
    resize: none !important;
}
#sources-card textarea {
    border: none !important;
    background: transparent !important;
    color: #7a8aaa !important;
    font-size: 0.82rem !important;
    line-height: 1.7 !important;
    resize: none !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
}

/* ── section labels ── */
#answer-label, #sources-label {
    color: #4f6ef7 !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin-bottom: 8px !important;
}

/* ── footer ── */
#footer {
    text-align: center;
    color: #3a4560;
    font-size: 0.75rem;
    margin-top: 20px;
    padding-bottom: 16px;
}
"""

def handle_query(question: str) -> tuple[str, str]:
    if not question.strip():
        return "Please enter a question.", ""

    result = ask(question)

    answer = result["answer"]
    if result.get("warning"):
        answer = f"{result['warning']}\n\n{answer}"

    sources = "\n".join(
        f"• {s['title']}\n  {s['url']}"
        for s in result["sources"]
    )

    return answer, sources


with gr.Blocks(title="EMU Housing Guide", css=CSS, theme=gr.themes.Base()) as demo:

    # ── header ────────────────────────────────────────────────────────────────
    gr.HTML("""
        <div id="header">
            <h1>🏠 EMU Unofficial Housing Guide</h1>
            <p>Ask anything about off-campus housing in Ypsilanti &mdash;
               answers are grounded in real resident reviews.</p>
        </div>
    """)

    # ── input + examples ──────────────────────────────────────────────────────
    with gr.Group(elem_id="input-card"):
        question_box = gr.Textbox(
            label="Your question",
            placeholder="e.g. What do residents say about BEAL properties?",
            lines=2,
            show_label=True,
        )
        ask_btn = gr.Button("Ask", variant="primary", elem_id="ask-btn")

        gr.HTML("<div style='margin:16px 0 8px;color:#5a6a8a;font-size:0.78rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;'>Try an example</div>")
        with gr.Row():
            for eq in EXAMPLE_QUESTIONS:
                gr.Button(eq, size="sm", elem_classes="example-btn").click(
                    fn=lambda q=eq: q,
                    outputs=question_box,
                )

    # ── outputs ───────────────────────────────────────────────────────────────
    with gr.Row():
        with gr.Column(scale=3):
            with gr.Group(elem_id="answer-card"):
                gr.HTML("<div id='answer-label'>Answer</div>")
                answer_box = gr.Textbox(
                    label="",
                    lines=8,
                    interactive=False,
                    show_label=False,
                    placeholder="Your answer will appear here…",
                )

        with gr.Column(scale=2):
            with gr.Group(elem_id="sources-card"):
                gr.HTML("<div id='sources-label'>Retrieved from</div>")
                sources_box = gr.Textbox(
                    label="",
                    lines=8,
                    interactive=False,
                    show_label=False,
                    placeholder="Sources will appear here…",
                )

    gr.HTML("<div id='footer'>Answers are grounded in retrieved documents only · EMU Unofficial Guide</div>")

    # ── events ────────────────────────────────────────────────────────────────
    ask_btn.click(handle_query, inputs=question_box, outputs=[answer_box, sources_box])
    question_box.submit(handle_query, inputs=question_box, outputs=[answer_box, sources_box])


if __name__ == "__main__":
    demo.launch()
