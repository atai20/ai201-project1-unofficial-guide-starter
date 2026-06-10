# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env            # Add your Groq API key
python build_index.py             # Build vector index (first run)
python app.py                     # Launch Gradio UI at http://localhost:7860
python evaluate.py                # Run all 5 evaluation questions
```

---

## Domain

**UC Berkeley unofficial student knowledge: dining halls, on-campus housing, off-campus rentals, CS course reviews, and campus survival tips.**

Official university sites list dining hours, housing deadlines, and course prerequisites — but they do not capture what students actually experience: 20-minute lunch lines at Crossroads, which CS professor gives written feedback on style points, or which off-campus blocks have recurring mold complaints. That knowledge lives in Reddit threads, Rate My Professors reviews, and student-compiled FAQs scattered across the web. This RAG system makes that fragmented insider knowledge searchable with plain-language questions and cited answers.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | r/berkeley dining thread | Reddit (saved text) | documents/reddit_crossroads_dining.txt |
| 2 | r/berkeley dining thread | Reddit (saved text) | documents/reddit_foothill_dining.txt |
| 3 | r/berkeley dining thread | Reddit (saved text) | documents/reddit_clark_kerr_dining.txt |
| 4 | Rate My Professors | Professor reviews | documents/rmp_cs61a_de_novo.txt |
| 5 | Rate My Professors | Professor reviews | documents/rmp_cs61b_hug.txt |
| 6 | Rate My Professors | Professor reviews | documents/rmp_cs70_wu_yan.txt |
| 7 | Housing forum FAQ | Student-compiled guide | documents/housing_lottery_guide.txt |
| 8 | r/berkeley housing thread | Reddit (saved text) | documents/off_campus_southside_housing.txt |
| 9 | r/berkeley transit thread | Reddit (saved text) | documents/reddit_bear_transit_tips.txt |
| 10 | Orientation Discord / wiki | Survival guide | documents/freshman_survival_guide.txt |
| 11 | r/berkeley clubs thread | Reddit (saved text) | documents/reddit_rso_recommendations.txt |
| 12 | Rate My Professors | Upper-division EECS reviews | documents/rmp_eecs_upper_div.txt |

**Ingestion pipeline:** `ingest.py` loads all `.txt` files from `documents/`, strips boilerplate headers (`Source:`, `Thread collected`, etc.), removes HTML entities, and collapses excess whitespace. Documents are saved as UTF-8 plain text — no live scraping required at query time.

---

## Chunking Strategy

**Chunk size:** 450 characters (~90–110 tokens)

**Overlap:** 80 characters

**Why these choices fit your documents:**

Documents mix short Reddit posts (1–4 sentences) with multi-paragraph FAQ entries. At 450 characters, most individual posts stay intact while longer guides split at paragraph or sentence boundaries. Overlap of 80 characters preserves context when a fact spans chunk boundaries (e.g., a dining hall name at the end of one chunk and the wait-time detail in the next). The splitter in `chunk.py` prefers `\n\n` paragraph breaks, then sentence boundaries, before hard character cuts.

**Final chunk count:** 53 chunks across 12 documents

### Sample Chunks

**Chunk 1** — `reddit_crossroads_dining.txt` (chunk 0)
```
u/calfoodie23: Crossroads is the biggest dining hall on campus and it shows. Lunch rush between 12-1:30 is brutal — expect 20-25 minute waits for hot food unless you go before noon or after 2. The salad bar is actually decent and usually has shorter lines. Their stir-fry station is popular but runs out of protein fast during peak hours.
```

**Chunk 2** — `rmp_cs61b_hug.txt` (chunk 1)
```
Review 2: Best feedback of any CS prof I've had. Autograder gives partial credit but Hug's written feedback on style points actually helps you improve. Go to his office hours even if you don't have questions — he remembers faces.
```

**Chunk 3** — `housing_lottery_guide.txt` (chunk 0)
```
Q: Is the housing lottery actually random? A: Partially. Berkeley Housing assigns a random lottery number to every applicant within their class year ( freshman, sophomore, etc.). You pick room groups before the lottery opens. When your number comes up, you select from remaining rooms in real time.
```

**Chunk 4** — `off_campus_southside_housing.txt` (chunk 1)
```
u_mold_warning: WARNING — several units in the Dwight-telegraph corridor have had mold complaints posted on the Berkeley Tenant's Union site. Ask landlords about ventilation and recent remediation. If you smell musty during tour, leave. Document everything with photos at move-in.
```

**Chunk 5** — `rmp_eecs_upper_div.txt` (chunk 0)
```
Review 1: Projects are the course. Pintos project takes 40+ hours. Start project 2 the day it's released. Exams are open-note but time-pressured. TAs run essential section reviews the week before midterms.
```

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers (384-dimensional embeddings, runs locally on CPU)

**Production tradeoff reflection:**

For a production deployment serving real Berkeley students, I would weigh: **(1) Domain accuracy** — models like `e5-large-v2` or OpenAI `text-embedding-3-large` better capture informal slang ("RMP", "Pintos", "meal swipe"); **(2) Multilingual support** — MiniLM is English-centric, but many students post in mixed languages; **(3) Context length** — if chunks grow to full forum threads, models supporting 512+ token inputs per embedding would help; **(4) Latency vs. cost** — MiniLM is free and ~50ms locally, while API embeddings add network latency but scale horizontally; **(5) Hybrid search** — production systems often combine embeddings with BM25 keyword search for course codes like "CS 61B" that embeddings may treat loosely.

---

## Retrieval Test Results

### Query 1: "What do students say about wait times at Crossroads during lunch?"

| Rank | Distance | Source | Excerpt |
|------|----------|--------|---------|
| 1 | 0.383 | reddit_crossroads_dining.txt | "Lunch rush between 12-1:30 is brutal — expect 20-25 minute waits for hot food..." |
| 2 | 0.534 | reddit_crossroads_dining.txt | "...Crossroads has the best dessert rotation on campus..." |

**Why relevant:** Top chunk directly answers the question with specific wait times (20–25 minutes) and time windows (12–1:30 pm). The second chunk is from the same document and adds Crossroads-specific context.

### Query 2: "Is the Berkeley housing lottery completely random?"

| Rank | Distance | Source | Excerpt |
|------|----------|--------|---------|
| 1 | 0.146 | housing_lottery_guide.txt | "Q: Is the housing lottery actually random? A: Partially..." |
| 2 | 0.393 | housing_lottery_guide.txt | "...re-applicants who lived on campus the prior year get priority..." |

**Why relevant:** The FAQ document contains an exact semantic match to the question. Distance 0.146 indicates strong similarity. Second chunk adds the priority-tier detail needed for a complete answer.

### Query 3: "Which CS professor gives the most useful feedback?"

| Rank | Distance | Source | Excerpt |
|------|----------|--------|---------|
| 1 | 0.491 | rmp_cs61b_hug.txt | "Best feedback of any CS prof I've had. Autograder gives partial credit but Hug's written feedback on style points actually helps you improve." |
| 2 | 0.503 | rmp_cs61a_de_novo.txt | General CS 61A advice about homework and discussions |

**Why relevant:** Top chunk explicitly names Hug and describes his feedback quality. Second chunk is partially relevant (CS-related) but does not answer the feedback question — illustrates cross-topic noise in a mixed corpus.

---

## Grounded Generation

**System prompt grounding instruction:**

The system prompt in `query.py` enforces five strict rules:
1. Answer ONLY from provided document excerpts
2. If insufficient information, respond exactly: *"I don't have enough information on that in my documents."*
3. Cite source filenames inline, e.g. `(source: reddit_foothill_dining.txt)`
4. Do not invent facts not present in excerpts
5. Keep answers concise (2–4 sentences)

Temperature is set to 0.1 to reduce hallucination. Retrieved chunks are formatted with explicit `[Excerpt N | source: filename | chunk index]` headers so the LLM cannot claim ignorance of which text it is using.

**How source attribution is surfaced in the response:**

Sources are attributed two ways: **(1)** the LLM is instructed to cite filenames inline in its answer, and **(2)** `query.py` programmatically appends `Retrieved from: filename1, filename2` if the model omits citations. The Gradio UI also displays a separate "Retrieved from" field listing all source documents.

### Example Responses

**Query:** "What do students say about wait times at Crossroads during lunch?"

**Answer:** According to student reviews (source: reddit_crossroads_dining.txt), Crossroads lunch rush between 12–1:30 pm brings 20–25 minute waits for hot food. Lines are shorter before noon, after 2 pm, or at the salad bar.

**Retrieved from:** reddit_crossroads_dining.txt

---

**Query:** "Is the Berkeley housing lottery completely random?"

**Answer:** No. The housing lottery FAQ (source: housing_lottery_guide.txt) explains that lottery numbers are randomly assigned within each class year, but re-applicants who lived on campus the prior year receive priority over new applicants. Disabled students and athletes are assigned through separate processes outside the general lottery.

**Retrieved from:** housing_lottery_guide.txt

---

**Out-of-scope query:** "What is the best pizza place in Berkeley?"

**Answer:** I don't have enough information on that in my documents.

*(No pizza restaurants appear in the corpus. The grounding prompt instructs the LLM to refuse rather than use general knowledge.)*

---

## Query Interface

**Launch:** `python app.py` → opens Gradio at `http://localhost:7860`

| Field | Description |
|-------|-------------|
| **Your question** | Text input for plain-language questions about Berkeley student life |
| **Ask** button | Submits the query (Enter key also works) |
| **Answer** | Grounded response with inline source citations |
| **Retrieved from** | Bulleted list of source document filenames |

**Example interaction:**

```
Your question: What mold warnings exist for off-campus housing?

Answer: Students warn (source: off_campus_southside_housing.txt) that several units in the 
Dwight-Telegraph corridor have had mold complaints. They recommend asking landlords about 
ventilation, leaving if you smell musty odors during a tour, and documenting conditions 
with photos at move-in.

Retrieved from:
• off_campus_southside_housing.txt
```

Built-in example questions are provided via Gradio's Examples widget for demo use.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Wait times at Crossroads during lunch? | 20–25 min waits, 12–1:30 pm rush; shorter lines before noon or at salad bar | Correctly cites 20–25 minute waits during 12–1:30 lunch rush from reddit_crossroads_dining.txt | Relevant | Accurate |
| 2 | Which CS professor gives the most useful feedback? | Josh Hug (CS 61B) — autograder feedback, style comments, office hours | Identifies Josh Hug with detailed feedback praise from rmp_cs61b_hug.txt | Partially relevant | Accurate |
| 3 | Is the housing lottery completely random? | No — random within class year but priority tiers for re-applicants; separate processes for athletes/disabled students | Explains partial randomness and priority tiers from housing_lottery_guide.txt | Relevant | Accurate |
| 4 | Mold warnings for off-campus housing? | Dwight-Telegraph corridor mold complaints; check ventilation, musty smells, document move-in | Correctly cites Dwight-Telegraph mold warnings from off_campus_southside_housing.txt | Relevant | Accurate |
| 5 | CS 162 Pintos project hours? | 40+ hours; start project 2 the day it is released | States 40+ hours and early start advice from rmp_eecs_upper_div.txt | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "What do students say about wait times at Crossroads during lunch?"

**What the system returned:** The answer correctly described Crossroads wait times, but retrieval also returned chunks from `reddit_clark_kerr_dining.txt` (distance 0.547) mentioning "wait times are basically zero" for Clark Kerr — a different dining hall.

**Root cause (tied to a specific pipeline stage):** **Retrieval stage** — the corpus mixes multiple dining hall documents that all discuss "wait times." Semantic embedding with `all-MiniLM-L6-v2` clusters conceptually similar text, so a Crossroads-specific query also retrieves Clark Kerr content because both chunks discuss dining hall wait times with similar vocabulary. The LLM must filter irrelevant halls from the prompt context.

**What you would change to fix it:** Add **metadata filtering** (stretch feature) so users can filter by subtopic (e.g., `dining_hall=crossroads`), or include the dining hall name prominently at the start of each chunk during ingestion. Hybrid BM25 search would also boost chunks containing the exact token "Crossroads."

---

## Spec Reflection

**One way the spec helped you during implementation:**

Writing the chunking strategy (450 chars, 80 overlap) before coding forced me to inspect document structure first. I noticed Reddit posts are short while the housing FAQ is long — that justified paragraph-aware splitting instead of naive fixed-width cuts. The evaluation plan in planning.md also gave concrete targets to test retrieval against before adding generation.

**One way your implementation diverged from the spec, and why:**

The spec planned top-k=5 retrieval, which I kept, but I added programmatic source attribution appended after LLM generation rather than relying solely on the model to cite sources. During testing, the LLM occasionally omitted filenames even when instructed to include them. Appending `Retrieved from:` programmatically guarantees attribution on every response.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Documents table, Chunking Strategy section (450 chars, 80 overlap, paragraph-first splitting), and architecture diagram from planning.md
- *What it produced:* Initial `ingest.py` and `chunk.py` with fixed-width splitting only
- *What I changed or overrode:* Added paragraph and sentence boundary splitting before hard character cuts, because fixed-width alone was breaking Reddit usernames from their posts mid-line

**Instance 2**

- *What I gave the AI:* Retrieval Approach section, grounding requirements, Groq model name, and the Gradio skeleton from the assignment instructions
- *What it produced:* `query.py` with a system prompt and `app.py` with basic Gradio Blocks
- *What I changed or overrode:* Added programmatic source attribution after generation (the model skipped citations on some runs), set temperature to 0.1 instead of default 1.0, and added a retrieval-only fallback mode when `GROQ_API_KEY` is not configured

---

## Project Structure

```
documents/           # 12 source text files
ingest.py            # Load and clean documents
chunk.py             # Chunking (450 chars, 80 overlap)
store.py             # Embed with MiniLM, store in ChromaDB
retrieve.py          # Semantic search (top-k=5)
query.py             # Grounded generation via Groq
app.py               # Gradio web interface
build_index.py       # One-command index builder
evaluate.py          # Run 5-question evaluation plan
planning.md          # Spec written before implementation
```
