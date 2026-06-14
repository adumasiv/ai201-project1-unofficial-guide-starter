# The Unofficial Guide — Project 1

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

Sample Chunks
First 5 chunks from source '1':

  [0] 300 chars | url: https://www.reddit.com/r/ypsi/comments/16brlnh/looking_for_apartments_advice/
  "Looking for apartments, advice?\n\nI am looking for a 1bed 1bath apartment in the Ypsi area. (For <= $1,200) After snooping around on here and on Google here are the results I've gotten so far:\n\nActually decent apartments:\n\nLakeshore Apartments\nChestnut Lake\nPines of Cloverlane (not 100% sure)\nShitbox"

  [1] 299 chars | url: https://www.reddit.com/r/ypsi/comments/16brlnh/looking_for_apartments_advice/
  't Lake\nPines of Cloverlane (not 100% sure)\nShitboxes: (crime, poor maintenance, terrible staff, etc.)\n\nAspen Chase, Schooner Cove (anything with Mckinley really)\nArbor One\nCountry Meadows Apartments\nHuron Heights\nSix Trails Apartments\nWaverly on the Lake\nNot enough info on:\n\nRed Lion\nHarris & Cross'

  [2] 300 chars | url: https://www.reddit.com/r/ypsi/comments/16brlnh/looking_for_apartments_advice/
  "Lake\nNot enough info on:\n\nRed Lion\nHarris & Cross\nSo far it seems like my only realistic choice by a longshot is Lakeshore but I'd like a second opinion. Are there any decent apartments that I haven't found yet?\nYeah your list seems pretty accurate, Lakeshore is pretty much the best affordable place"

  [3] 300 chars | url: https://www.reddit.com/r/ypsi/comments/16brlnh/looking_for_apartments_advice/
  "Lakeshore is pretty much the best affordable place.\n\nYou willing to branch out? There’s some decent places in Van Buren too by or just off the highway.\n\nYeah I'd be open to branching out. I'd say max 30 minutes out from Ann Arbor is my limit (I currently work there)\n\nSouthport and Tuscan Manor might"

  [4] 300 chars | url: https://www.reddit.com/r/ypsi/comments/16brlnh/looking_for_apartments_advice/
  "ntly work there)\n\nSouthport and Tuscan Manor might be worth checking out. Southport is nicer, Tuscan Manor is cheaper.\n\nNot sure how quick the commute would be during rush hour but it would be about 20-25 minutes normally.\n\nI can't speak to Southport but Westlake, owned by the same company, was a gr"

Chunks exceeding 300 chars: 0
50-char overlap preserved between chunk 0→1: True
---

## Embedding Model

**Embedding model:**
bge-large-en-v1.5
**Top-k:**
8
**Production tradeoff reflection:**
Accuracy on domain-specific text. Larger and more expensive models would give more accurate responces. If cost wasn't a constraint, accuracy would be valued above all. 

Retrieval Test Results

1. Your question: Should I rent from Apsen Chase?

Best match  (rerank score: 0.5035)
Source : r/ypsi - Affordable & safe apartments in ypsi?
URL    : https://www.reddit.com/r/ypsi/comments/1f5rrjj/affordable_safe_apartments_in_ypsi/

mates and I just signed a lease for a nice little house near Depot Town. It’s $1,500/month and we split it three ways. We found our place through Zillow!
ClassroomMother8062
I don't see aspen chase on here but I'd avoid it. Heard and seen really bad things about it, especially covid and post covid.

This is a relavent because it speaks directly to the the public reception of Aspen Chase.


2. Your question: Is depot town walkable?

Best match  (rerank score: 0.9763)
Source : r/ypsi - Moving to Ypsi
URL    : https://www.reddit.com/r/ypsi/comments/1ixyfzz/moving_to_ypsi/

super phased by "bad" neighborhoods. Good to get an idea from locals tho! Any input on stuff do/other recs is welcome as well :)

edit: wow thank you everyone! all these comments are so helpful, I'm taking notes and getting excited.
Normal Park and Depot Town are walkable to campus and great neighbo

This chunk is relavent because it directly answers the question being asked. 

3. Best match  (rerank score: 0.9508)
Source : r/ypsi - Moving to Ypsi
URL    : https://www.reddit.com/r/ypsi/comments/1ixyfzz/moving_to_ypsi/

ry safe in this area. North Hydro Park trail being within walking distance is a great bonus as well!
We live near it and the houses over here are also pretty nice too. Small and quiet neighbourhoods. But you definitely need a car if you live over here.
+1 for Lakeshore
What vibe are you looking for?
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

Example Responses:
Residents advise avoiding Beal properties, citing poor conditions and bad landlord experiences. Some properties owned by Beal are described as "mouse infested pissholes", while others may be nice, indicating a "MASSIVE variance" in quality. Multiple sources explicitly state "Do not rent from Beal" and "AVOID" their properties.
• r/ypsi - Moving to Ypsi
• r/AnnArbor - Good trouble-free apartment complexes for EMU student

According to the sources, Aspen Chase is described as "fine" by one resident who lived there from 2018-2022, while another resident who lived there from 2010-2017 thought it "wasn't the best; it wasn't the worst." Chestnut Lake, on the other hand, is consistently described as "really nice" and "surprisingly very quiet," with renters saying it's "highly rated." However, it's also mentioned that Chestnut Lake is "way over priced." Based on this information, Chestnut Lake may be a better option for a student due to its positive reviews, but the high price should be considered.
• r/ypsi - Affordable & safe apartments in ypsi?
• ApartmentRatings - Ypsilanti MI

---
## Query Interface

### Input and Output Fields

The web interface is built with Gradio and accessible at `http://localhost:7860` after running `app.py`.

**Input**
| Field | Description |
|-------|-------------|
| Your question | A free-text box where the user types any housing-related question. Supports multi-line input. Submits on Enter or by clicking the Ask button. |
| Example questions | Five pre-written pill buttons that auto-fill the question box with a common query. Clicking one populates the field — the user can then edit or submit as-is. |

**Output**
| Field | Description |
|-------|-------------|
| Answer | The model's response, generated strictly from the retrieved documents. If the retrieved chunks all come from one source, a one-sided retrieval warning is prepended to the answer. |
| Retrieved from | A list of the sources the answer was drawn from, showing each source's title and original URL. Attribution is extracted programmatically from chunk metadata — the model does not generate citations. |

---

### Sample Interaction

**Question entered:**
What do residents say about BEAL properties?
**Answer returned:**
Residents strongly advise against renting from BEAL properties. According to
"Reddit - r/ypsi - Looking for apartments, advice?", BEAL is described as one
of the worst landlords in Ypsilanti, with reports of ignored maintenance
requests, poor communication, and properties in poor condition. Multiple
reviewers explicitly warn others to avoid them entirely.
• Reddit - r/ypsi - Looking for apartments, advice?
https://www.reddit.com/r/ypsi/comments/16brlnh/looking_for_apartments_advice/

• Reddit - r/ypsi - Affordable & safe apartments in ypsi?
https://www.reddit.com/r/ypsi/comments/1f5rrjj/affordable_safe_apartments_in_ypsi/

**Retrieved from:**

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
