# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain
Off-campus housing reviews for Eastern Michigan University — useful because roughly 75% of EMU students are commuters and live in unaffiliated housing throughout the surrounding area. Finding reliable information can be difficult because official housing websites primarily showcase marketing photos and curated reviews, which may not accurately reflect the actual living experience, property management quality, safety, maintenance responsiveness, noise levels, or overall value. As a result, students who choose housing based solely on information provided by housing websites can be led astray.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 |Reddit - r/ypsi - Looking for apartments, advice?|Website |https://www.reddit.com/r/ypsi/comments/16brlnh/looking_for_apartments_advice/ |
| 2 |Reddit - r/ypsi |Website - Moving to Ypsi|https://www.reddit.com/r/ypsi/comments/1ixyfzz/moving_to_ypsi/ |
| 3 |Reddit - r/AnnArbor - Good, trouble-free apartment complexes for EMU student|Website |https://www.reddit.com/r/AnnArbor/comments/wtibvu/good_troublefree_apartment_complexes_for_emu/ |
| 4 |ApartmentRatings |Website |https://www.apartmentratings.com/mi/ypsilanti/ |
| 5 |Yelp - apartments Ypsilanti, MI |Website |https://www.yelp.com/search?find_desc=apartments&find_loc=Ypsilanti%2C+MI |
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
**Why these choices fit your documents:**
The documents used are long reddit forum based documents. This warrants a longer character chunk to keep the ideas of each paragraph together. The overlap is a little more than 15% of the chunk to preserve the context of the average sentence length in a reddit post.
**Final chunk count:**
281
---

## Embedding Model

**Embedding model:**
bge-large-en-v1.5
**Top-k:**
8
**Production tradeoff reflection:**
Accuracy on domain-specific text. Larger and more expensive models would give more accurate responces. If cost wasn't a constraint, accuracy would be valued above all. 
---

## Grounded Generation

**System prompt grounding instruction:**
You are a helpful assistant for the EMU Unofficial Housing Guide.
Answer the question using only the information in the provided documents.
Do not use prior knowledge, training data, or any outside information.
If the documents don't contain enough information to answer, say exactly:
"I don't have enough information on that."
Every statement in your answer must be supported by the documents below.
Be concise: answer in 2-5 sentences.

**How source attribution is surfaced in the response:**
In responses, source attribution surfaces at the end in a currated list of sources. It displays all of the sources it pulled from to answer. 
---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 |What do residents say about BEAL properties? |Do not rent from these properties. |Residents advise avoiding Beal properties |Relavent |Accurate |
| 2 |What do residents say about the Depot Town area? |Nice with affordable rent. |Residents describe Depot Town as the "most ideal" area |Relavent |Accurate |
| 3 |Would past residents recommend living at Lakeshore? |Yes, they would recommend it. |Yes, past residents would recommend living at Lakeshore. |Relavent |Accurate |
| 4 |Is the community around Lakeshore walkable? |No, you need a car to get places. |The community around Lakeshore is not considered walkable |Relavent |Accurate |
| 5 |Should a student rent at Aspen Chase or Waverly on the Lake? |Waverly on the Lake. |Waverly on the lake is considered better but is still on the list of places to avoid. |Relavent |Partially Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:**
Which apartment is closest to campus?
**What the system returned:**
According to the documents, Red Lion apartments are less than 5 minutes from campus, making them one of the closest options. Additionally, an apartment that is closest to the campus is considered safest, as EMU police are nearby. Another option is Barnes, which is one of the better rental companies around campus.
**Root cause (tied to a specific pipeline stage):**
The root came in the document ingestion stage. The documents provide little detail when it comes to proximity to campus. So the only option that mentions it gets flagged.
**What you would change to fix it:**
I would add more documents about housing location in relation to campus.
---

## Spec Reflection

**One way the spec helped you during implementation:**
It made me slow down production and really plan out what I need to develop. There was intention put behind all the steps. Also, having a set plan before development helped me with comprehension with what the AI wrote.
**One way your implementation diverged from the spec, and why:**
My implementation diverged from my plan during chunking. Originally the plan was to have a overlap of 60 characters. But, during working with the model it proved to be unneccesary. The overlap was adjusted down to the sweet spot of 50 characters.
---

## AI Usage

**Instance 1**

- *What I gave the AI:* I gave Claude my Chunking Strategy section from planning.md and asked it to implement chunk_text().
- *What it produced:* It returned a function using a fixed character split.
- *What I changed or overrode:* I overrode the chunk size from 60 to 50 because during testing the extra 10 characters became redundant. 50 characters performed with the same accuracy.

**Instance 2**

- *What I gave the AI:* I gave Claude my retrieval approach section from planning.md and asked it to implement mbed_and_store().
- *What it produced:* It produced a function that used my eval test questions as the questions to test the retieval every time.
- *What I changed or overrode:* I overrode the static questions and implemented the program to prompt the user to give a question.
