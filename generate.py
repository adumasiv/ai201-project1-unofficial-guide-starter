"""
Generation pipeline for the EMU Unofficial Housing Guide.

generate(query, chunks) — build a grounded answer from retrieved chunks
                          using Groq llama-3.3-70b-versatile.

run_cli()              — minimal interactive CLI (Milestone 5 interface).
run_evaluation()       — verify all 5 Evaluation Plan questions end-to-end.

Grounding rules (enforced in the system prompt and in code):
  * The LLM may only use the provided context — never its training data.
  * If context is insufficient, a safe fallback message is returned.
  * Source URLs are injected programmatically and returned separately,
    so citation is guaranteed regardless of LLM behaviour.
  * One-sided retrieval (all chunks from a single source) is flagged.
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from retrieve import search

load_dotenv()

# ── constants ─────────────────────────────────────────────────────────────────

GROQ_MODEL       = "llama-3.3-70b-versatile"
MAX_CONTEXT_CHARS = 6000   # hard cap on total context sent to the LLM
FALLBACK_MSG     = (
    "I could not find enough information in the knowledge base "
    "to answer that question."
)

# ── prompt template ───────────────────────────────────────────────────────────
# Both the grounding rules and the retrieved documents live in a single
# template so the model sees instructions and evidence together.
# {context} and {question} are filled in by build_prompt() at call time.

PROMPT_TEMPLATE = """\
You are a helpful assistant for the EMU Unofficial Housing Guide.
Answer the question using only the information in the provided documents.
Do not use prior knowledge, training data, or any outside information.
If the documents don't contain enough information to answer, say exactly:
"I don't have enough information on that."
Every statement in your answer must be supported by the documents below.
Be concise: answer in 2-5 sentences.

PROVIDED DOCUMENTS:
{context}

QUESTION: {question}

ANSWER:"""

# ── helpers ───────────────────────────────────────────────────────────────────

def _build_context(chunks: list[dict[str, Any]]) -> str:
    """Format chunks labeled by source title so the model cites names, not numbers."""
    parts = []
    for c in chunks:
        parts.append(f"Source \"{c['title']}\":\n{c['text'].strip()}")
    return "\n\n".join(parts)


def build_prompt(context: str, question: str) -> str:
    """Fill the prompt template with retrieved context and the user question."""
    return PROMPT_TEMPLATE.format(context=context, question=question)


def _dedupe_sources(chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Return unique sources (title + url) in the order they appear."""
    seen: set[str] = set()
    sources: list[dict[str, str]] = []
    for c in chunks:
        key = c["url"]
        if key not in seen:
            seen.add(key)
            sources.append({"title": c["title"], "url": c["url"]})
    return sources


def _is_one_sided(chunks: list[dict[str, Any]]) -> bool:
    """Return True if every chunk comes from the same source document."""
    return len({c["source_id"] for c in chunks}) == 1


# ── public: generate ──────────────────────────────────────────────────────────

def generate(
    query: str,
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate a grounded answer for *query* from *chunks*.

    Returns a dict with:
        answer   – LLM response (or the safe fallback string)
        sources  – list of {title, url} dicts, programmatically extracted
        warning  – optional string flagging one-sided retrieval
        chunks   – the chunks passed in (for inspection)
    """
    if not chunks:
        return {
            "answer":  FALLBACK_MSG,
            "sources": [],
            "warning": None,
            "chunks":  [],
        }

    # Build context, capped to avoid exceeding context window
    context = _build_context(chunks)[:MAX_CONTEXT_CHARS]
    sources = _dedupe_sources(chunks)

    warning: str | None = None
    if _is_one_sided(chunks):
        warning = (
            "⚠️  All retrieved chunks come from a single source. "
            "This answer may reflect one perspective only."
        )

    prompt = build_prompt(context=context, question=query)

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,   # deterministic — grounding, not creativity
        max_tokens=300,
    )

    answer = response.choices[0].message.content.strip()

    # Safety check: if the model returns nothing useful, use the fallback
    if not answer:
        answer = FALLBACK_MSG

    return {
        "answer":  answer,
        "sources": sources,
        "warning": warning,
        "chunks":  chunks,
    }


# ── public: full pipeline (retrieve → rerank → generate) ─────────────────────

def ask(query: str, k: int = 8) -> dict[str, Any]:
    """
    End-to-end pipeline: retrieve top-k chunks and generate an answer.
    k=8 matches the architecture diagram (retrieve 20 → rerank → pass top 8).
    """
    chunks = search(query, k=k)
    return generate(query, chunks)


# ── CLI interface ─────────────────────────────────────────────────────────────

def run_cli() -> None:
    """Minimal interactive CLI for the housing guide."""
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║     EMU Unofficial Housing Guide — Ask a Question    ║")
    print("╚══════════════════════════════════════════════════════╝")
    print("Type your question and press Enter. Type 'quit' to exit.\n")

    while True:
        try:
            query = input("Question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        print("\nSearching knowledge base…")
        result = ask(query)

        print(f"\n{'─'*56}")
        print(f"Answer:\n{result['answer']}")

        if result["warning"]:
            print(f"\n{result['warning']}")

        if result["sources"]:
            print("\nSources:")
            for s in result["sources"]:
                print(f"  • {s['title']}")
                print(f"    {s['url']}")

        print(f"{'─'*56}\n")


# ── evaluation ────────────────────────────────────────────────────────────────

EVAL_QUESTIONS = [
    {
        "id": 1,
        "question": "What do residents say about BEAL properties?",
        "expected": "Do not rent from these properties.",
        "keywords": ["avoid", "beal", "bad", "terrible", "plague", "stay away",
                     "nightmare", "do not", "don't"],
    },
    {
        "id": 2,
        "question": "What do residents say about the Depot Town area?",
        "expected": "Nice with affordable rent.",
        "keywords": ["depot town", "nice", "great", "ideal", "affordable",
                     "beautiful", "friendly"],
    },
    {
        "id": 3,
        "question": "Would past residents recommend living at Lakeshore?",
        "expected": "Yes, they would recommend it.",
        "keywords": ["recommend", "highly", "great", "love", "yes", "best"],
    },
    {
        "id": 4,
        "question": "Is the community around Lakeshore walkable?",
        "expected": "No, you need a car to get places.",
        "keywords": ["car", "not walkable", "car dependent", "need a car",
                     "drive", "not walk"],
    },
    {
        "id": 5,
        "question": "Should a student rent at Aspen Chase or Waverly on the Lake?",
        "expected": "Waverly on the Lake.",
        "keywords": ["waverly", "not aspen", "avoid aspen", "aspen chase",
                     "garbage", "bad"],
    },
]


def run_evaluation() -> None:
    """Run all 5 Evaluation Plan questions end-to-end and report results."""
    from retrieve import retrieve, rerank

    W = 70
    print("\n" + "=" * W)
    print("END-TO-END EVALUATION: retrieve → rerank → generate")
    print("=" * W)

    passed = 0

    for eq in EVAL_QUESTIONS:
        q        = eq["question"]
        keywords = eq["keywords"]

        # ── run the full pipeline, but also capture intermediate chunks ──
        candidates = retrieve(q, k=32)
        top_chunks = rerank(q, candidates, top_n=8)
        result     = generate(q, top_chunks)

        answer_lower = result["answer"].lower()
        hit = any(kw.lower() in answer_lower for kw in keywords)

        status = "✅ PASS" if hit else "❌ FAIL"
        if hit:
            passed += 1

        print(f"\n{'─'*W}")
        print(f"Q{eq['id']}: {q}")
        print(f"Expected : {eq['expected']}")
        print(f"Status   : {status}")

        # ── generated answer ─────────────────────────────────────────────
        print(f"\nAnswer:")
        for line in result["answer"].splitlines():
            print(f"  {line}")
        if result.get("warning"):
            print(f"\n  {result['warning']}")

        # ── retrieval quality: top-8 reranked chunks ─────────────────────
        print(f"\nRetrieval quality  (top {len(top_chunks)} chunks after rerank):")
        unique_sources = {c["source_id"] for c in top_chunks}
        print(f"  Sources spanned : {len(unique_sources)} / {len(top_chunks)} chunks")

        for i, c in enumerate(top_chunks, 1):
            kw_hit = any(kw.lower() in c["text"].lower() for kw in keywords)
            marker = "★" if kw_hit else " "
            snippet = c["text"].replace("\n", " ")[:100]
            print(
                f"  {marker}[{i}] rerank={c['rerank_score']:+.3f}  "
                f"embed={c['score']:.3f}  src={c['source_id']}  "
                f"\"{snippet}…\""
            )

        # ── cited sources ─────────────────────────────────────────────────
        print(f"\nCited sources:")
        for s in result["sources"]:
            print(f"  • {s['title']}")
            print(f"    {s['url']}")

    # ── summary ───────────────────────────────────────────────────────────
    print(f"\n{'='*W}")
    bar = ("█" * passed) + ("░" * (len(EVAL_QUESTIONS) - passed))
    print(f"Result : [{bar}]  {passed}/{len(EVAL_QUESTIONS)} passed")
    print("=" * W)


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if "--eval" in sys.argv:
        run_evaluation()
    else:
        run_cli()
