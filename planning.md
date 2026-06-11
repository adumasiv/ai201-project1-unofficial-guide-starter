# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

Off-campus housing reviews for Eastern Michigan University — useful because roughly 75% of EMU students are commuters and live in unaffiliated housing throughout the surrounding area. Finding reliable information can be difficult because official housing websites primarily showcase marketing photos and curated reviews, which may not accurately reflect the actual living experience, property management quality, safety, maintenance responsiveness, noise levels, or overall value. As a result, students who choose housing based solely on information provided by housing websites can be led astray.

---

## Documents

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 |Reddit - r/ypsi - Looking for apartments, advice?|Website |https://www.reddit.com/r/ypsi/comments/16brlnh/looking_for_apartments_advice/ |
| 2 |Reddit - r/ypsi |Website - Moving to Ypsi|https://www.reddit.com/r/ypsi/comments/1ixyfzz/moving_to_ypsi/ |
| 3 |Reddit - r/AnnArbor - Good, trouble-free apartment complexes for EMU student|Website |https://www.reddit.com/r/AnnArbor/comments/wtibvu/good_troublefree_apartment_complexes_for_emu/ |
| 4 |ApartmentRatings |Website |https://www.apartmentratings.com/mi/ypsilanti/ |
| 5 |Yelp - apartments Ypsilanti, MI |Website | |https://www.yelp.com/search?find_desc=apartments&find_loc=Ypsilanti%2C+MI
| 6 |Reddit - r/ypsi - Affordable & safe apartments in ypsi?|Website |https://www.reddit.com/r/ypsi/comments/1f5rrjj/affordable_safe_apartments_in_ypsi/ |
| 7 |Reddit - r/ypsi - Are there any high quality walkable apartments near downtown Ypsi or Depot Town?|Website |https://www.reddit.com/r/ypsi/comments/17k0bh7/are_there_any_high_quality_walkable_apartments/ |
| 8 |Niche - Eastern Michigan University |Website |https://www.niche.com/colleges/eastern-michigan-university/campus-life/ |
| 9 |Reddit - r/ypsi - Restaurant Recommendations?|Website |https://www.reddit.com/r/ypsi/comments/15s7rji/restaurant_recommendations/ |
| 10 |City of Ypsilant - Housing Affordability & Accessibility |Document |https://www.cityofypsilanti.com/DocumentCenter/View/1940/Open-Forum-Public-Slideshow?bidId= |

---

## Chunking Strategy

**Chunk size:**
300 character chunks.
**Overlap:**
50 characters
**Reasoning:**
The documents used are long reddit forum based documents. This warrants a longer character chunk to keep the ideas of each paragraph together. The overlap is a little more than 15% of the chunk to preserve the context of the average sentence length in a reddit post.
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
bge-large-en-v1.5
**Top-k:**
8
**Production tradeoff reflection:**
Accuracy on domain-specific text. Larger and more expensive models would give more accurate responces. If cost wasn't a constraint, accuracy would be valued above all. 
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 |What do residents say about BEAL properies? |Do not rent from these properties. |
| 2 |What do residents say about the Depot Town Area? |Nice with affordable rent. |
| 3 |Would past residents recommend living at Lakeshore? |Yes, they would recommend it. |
| 4 |Is the community around Lakeshore Walkable? |No, you need a car to get places. |
| 5 |Should a student rent an apartment at Aspen Chase or Waverly on the Lake?|Waverly on the Lake. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.Boundary splits severing sentiment pivots. The unregulated lengths of reddit post can either go way under or over 300 characters. So there is a risk that the chunks lose some context.

2.Upvoted opinions drowning out minority opinions. The way reddit is structured with the highest upvoted at the top have the chance of skewing results before retrieval

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

EMU Unofficial Guide — RAG Pipeline
─────────────────────────────────────────────────────────────────────────────────

 ┌─────────────┐    ┌──────────────────┐    ┌─────────────────────┐
 │  INGESTION  │    │    CHUNKING      │    │     EMBEDDING       │
 │             │    │                  │    │                     │
 │  10 Reddit  │───▶│  300 char chunks │───▶│  bge-large-en-v1.5  │
 │  Articles   │    │  60 char overlap │    │                     │
 │             │    │  (recommended)   │    │  ┌───────────────┐  │
 └─────────────┘    └──────────────────┘    │  │   ChromaDB    │  │
                                            │  │ Vector Store  │  │
                                            │  └───────────────┘  │
                                            └─────────────────────┘
                                                       │
                                                       ▼
                                            ┌─────────────────────┐
                                            │      RETRIEVAL      │
                                            │                     │
                                            │  Fetch  k = 20      │
                                            │       │             │
                                            │       ▼             │
                                            │  bge-reranker-large │
                                            │       │             │
                                            │       ▼             │
                                            │  Pass top k = 8     │
                                            └─────────────────────┘
                                                       │
                                                       ▼
                                            ┌─────────────────────┐
                                            │     GENERATION      │
                                            │                     │
                                            │  Groq               │
                                            │  llama-3.3-70b      │
                                            │  -versatile         │
                                            └─────────────────────┘
---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
- Give Claude the Documents table and Chunking Strategy section; ask it to produce ingest_documents() and chunk_text(text, chunk_size=300, overlap=50) with source URL metadata attached to each chunk
- Verify by inspecting 5 chunks from source #1 — confirm no chunk exceeds 300 chars, consecutive chunks share ~50 chars, and metadata is populated

**Milestone 4 — Embedding and retrieval:**
- Give Claude the Retrieval Approach section and Architecture diagram; ask it to implement embed_and_store() using bge-large-en-v1.5 into ChromaDB, retrieve(query, k=20), and rerank(query, chunks, top_n=8) using bge-reranker-large
- Verify by running all 5 Evaluation Plan questions through the full retrieve -> rerank pipeline and confirming the correct chunk surfaces in the top 8 for each

**Milestone 5 — Generation and interface:**
- Give Claude the Generation stage of the Architecture diagram, the Evaluation Plan, and the Anticipated Challenges section; ask it to implement generate(query, chunks) calling Groq llama-3.3-70b-versatile with a system prompt that cites source URLs and flags one-sided retrieval, plus a minimal CLI or Gradio interface
- Verify by running all 5 Evaluation Plan questions end-to-end and confirming each answer matches the expected answer and includes at least one cited source URL

