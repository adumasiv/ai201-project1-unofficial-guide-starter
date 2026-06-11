"""
Embedding, vector storage, and retrieval pipeline for the EMU Unofficial Housing Guide.

Three public functions:

    embed_and_store()          — chunk all documents, embed with bge-large-en-v1.5,
                                 persist to a local ChromaDB collection.

    retrieve(query, k=20)      — embed the query and return the top-k chunks
                                 by cosine similarity from ChromaDB.

    rerank(query, chunks, top_n=8)
                               — score each chunk with bge-reranker-large and
                                 return the top_n highest-scoring chunks.

Typical call order:
    embed_and_store()               # run once (or when documents change)
    chunks = retrieve(query)        # fetch k=20 candidates
    top    = rerank(query, chunks)  # rerank to top_n=8
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import CrossEncoder, SentenceTransformer

from ingest import chunk_documents

# ── constants ─────────────────────────────────────────────────────────────────

EMBED_MODEL_NAME   = "BAAI/bge-large-en-v1.5"
RERANK_MODEL_NAME  = "BAAI/bge-reranker-large"
COLLECTION_NAME    = "emu_housing"
CHROMA_DIR         = Path(__file__).parent / ".chroma"

# BGE embedding models expect this prefix on queries (not on stored documents).
BGE_QUERY_PREFIX   = "Represent this sentence for searching relevant passages: "

# ── lazy model singletons ─────────────────────────────────────────────────────

_embed_model:  SentenceTransformer | None = None
_rerank_model: CrossEncoder        | None = None


def _get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        print(f"[retrieve] Loading embedding model {EMBED_MODEL_NAME} …")
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    return _embed_model


def _get_rerank_model() -> CrossEncoder:
    global _rerank_model
    if _rerank_model is None:
        print(f"[retrieve] Loading reranker model {RERANK_MODEL_NAME} …")
        _rerank_model = CrossEncoder(RERANK_MODEL_NAME)
    return _rerank_model


# ── ChromaDB client ───────────────────────────────────────────────────────────

def _get_collection(reset: bool = False) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ── public: step 1 — embed and store ─────────────────────────────────────────

def embed_and_store(reset: bool = False) -> int:
    """
    Chunk all documents, embed each chunk with bge-large-en-v1.5, and upsert
    into a persistent ChromaDB collection.

    Pass reset=True to wipe and rebuild the collection from scratch.
    Returns the total number of chunks stored.
    """
    collection = _get_collection(reset=reset)

    # Skip if already populated and not resetting
    existing = collection.count()
    if existing > 0 and not reset:
        print(f"[embed] Collection already has {existing} chunks — skipping re-embed.")
        print("        Pass reset=True to force a rebuild.")
        return existing

    chunks = chunk_documents()
    if not chunks:
        raise RuntimeError("No chunks found. Run clean_documents.py then ingest.py first.")

    model = _get_embed_model()
    texts = [c["text"] for c in chunks]

    print(f"[embed] Embedding {len(texts)} chunks with {EMBED_MODEL_NAME} …")
    # Documents are encoded without the query prefix per BGE spec.
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).tolist()

    # Upsert in batches of 500 to stay within ChromaDB limits
    batch_size = 500
    for start in range(0, len(chunks), batch_size):
        batch_chunks     = chunks[start : start + batch_size]
        batch_embeddings = embeddings[start : start + batch_size]
        collection.upsert(
            ids        = [f"{c['source_id']}_{c['chunk_index']}" for c in batch_chunks],
            documents  = [c["text"]         for c in batch_chunks],
            embeddings = batch_embeddings,
            metadatas  = [
                {
                    "source_id":   c["source_id"],
                    "title":       c["title"],
                    "url":         c["url"],
                    "chunk_index": c["chunk_index"],
                }
                for c in batch_chunks
            ],
        )

    total = collection.count()
    print(f"[embed] Stored {total} chunks in ChromaDB at {CHROMA_DIR}")
    return total


# ── public: step 2 — retrieve ─────────────────────────────────────────────────

def retrieve(query: str, k: int = 20) -> list[dict[str, Any]]:
    """
    Embed *query* and return the top-k most similar chunks from ChromaDB.

    Each returned dict has: text, source_id, title, url, chunk_index, score.
    score is cosine similarity (higher = more similar).
    """
    model      = _get_embed_model()
    collection = _get_collection()

    query_embedding = model.encode(
        BGE_QUERY_PREFIX + query,
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[dict[str, Any]] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            {
                "text":        doc,
                "source_id":   meta["source_id"],
                "title":       meta["title"],
                "url":         meta["url"],
                "chunk_index": meta["chunk_index"],
                # ChromaDB returns cosine distance (0 = identical); convert to similarity.
                "score":       round(1 - dist, 4),
            }
        )

    return chunks


# ── public: step 3 — rerank ───────────────────────────────────────────────────

def rerank(
    query: str,
    chunks: list[dict[str, Any]],
    top_n: int = 8,
) -> list[dict[str, Any]]:
    """
    Score each chunk against *query* with bge-reranker-large and return the
    top_n highest-scoring chunks, sorted descending by rerank score.

    Adds a 'rerank_score' key to each returned chunk dict.
    """
    model = _get_rerank_model()

    pairs  = [(query, c["text"]) for c in chunks]
    scores = model.predict(pairs).tolist()

    ranked = sorted(
        [dict(c, rerank_score=round(s, 4)) for c, s in zip(chunks, scores)],
        key=lambda x: x["rerank_score"],
        reverse=True,
    )

    return ranked[:top_n]


# ── public: step 4 — search (full pipeline, single call) ─────────────────────

def search(query: str, k: int = 5) -> list[dict[str, Any]]:
    """
    Run the full retrieval pipeline for *query* and return the top-k results.

    Internally fetches k*4 candidates from ChromaDB (wider net improves
    reranker recall), reranks with bge-reranker-large, and returns the top-k.

    Each result dict contains:
        text         – the chunk text
        source_id    – document number (matches planning.md table)
        title        – human-readable source title
        url          – original URL for citation
        chunk_index  – position within the source document
        score        – cosine similarity from the embedding stage
        rerank_score – cross-encoder relevance score (higher = more relevant)
    """
    candidates = retrieve(query, k=k * 4)
    top        = rerank(query, candidates, top_n=k)
    return top


# ── evaluation ────────────────────────────────────────────────────────────────

EVAL_QUESTIONS = [
    {
        "id": 1,
        "question": "What do residents say about BEAL properties?",
        "expected": "Do not rent from these properties.",
        "keywords": ["beal", "avoid", "plague", "terrible", "bad", "nightmare"],
    },
    {
        "id": 2,
        "question": "What do residents say about the Depot Town area?",
        "expected": "Nice with affordable rent.",
        "keywords": ["depot town", "depot"],
    },
    {
        "id": 3,
        "question": "Would past residents recommend living at Lakeshore?",
        "expected": "Yes, they would recommend it.",
        "keywords": ["lakeshore", "lake shore"],
    },
    {
        "id": 4,
        "question": "Is the community around Lakeshore walkable?",
        "expected": "No, you need a car to get places.",
        "keywords": ["car", "walk", "walkable", "lakeshore", "lake shore"],
    },
    {
        "id": 5,
        "question": "Should a student rent an apartment at Aspen Chase or Waverly on the Lake?",
        "expected": "Waverly on the Lake.",
        "keywords": ["waverly", "aspen"],
    },
]


def run_evaluation() -> None:
    """
    Run all 5 evaluation questions through the full retrieve → rerank pipeline.
    Prints the top-8 chunks per question and whether the expected answer keywords
    appear in any of them.
    """
    print("\n" + "=" * 70)
    print("EVALUATION: retrieve(k=20) → rerank(top_n=8)")
    print("=" * 70)

    all_passed = True

    for eq in EVAL_QUESTIONS:
        q        = eq["question"]
        keywords = eq["keywords"]

        candidates = retrieve(q, k=20)
        top8       = rerank(q, candidates, top_n=8)

        # Check: does any top-8 chunk contain at least one expected keyword?
        combined_text = " ".join(c["text"].lower() for c in top8)
        hit = any(kw.lower() in combined_text for kw in keywords)

        status = "✅ PASS" if hit else "❌ FAIL"
        if not hit:
            all_passed = False

        print(f"\n{'─'*70}")
        print(f"Q{eq['id']}: {q}")
        print(f"Expected: {eq['expected']}")
        print(f"Result:   {status}")
        print(f"\nTop-8 chunks:")
        for i, c in enumerate(top8, 1):
            print(f"  [{i}] score={c['rerank_score']:>7.4f} | "
                  f"src={c['source_id']} chunk={c['chunk_index']} | "
                  f"{c['text'][:120].replace(chr(10), ' ')!r}")

    print(f"\n{'='*70}")
    print(f"{'All questions passed ✅' if all_passed else 'Some questions failed ❌ — review chunks above'}")
    print("=" * 70)


# ── interactive query prompt ──────────────────────────────────────────────────

def run_interactive() -> None:
    """
    Prompt the user for a question and print the single most relevant chunk.
    Type 'quit' or press Ctrl+C to exit.
    """
    print("\nEMU Housing Guide — ask a question (type 'quit' to exit)")
    print("-" * 55)

    while True:
        try:
            query = input("\nYour question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        results = search(query, k=1)

        if not results:
            print("No results found.")
            continue

        top = results[0]
        print(f"\nBest match  (rerank score: {top['rerank_score']:.4f})")
        print(f"Source : {top['title']}")
        print(f"URL    : {top['url']}")
        print(f"\n{top['text']}")


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    rebuild = "--rebuild" in sys.argv
    embed_and_store(reset=rebuild)

    # run_evaluation()   # hardcoded eval questions — uncomment to re-run
    run_interactive()
