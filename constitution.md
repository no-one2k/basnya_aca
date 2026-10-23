# ACA Constitution — Mission & Tech Stack

**ACA** = *Agent for Citation Augmentation.*

This is a **forward-looking vision document**. It describes where ACA is meant to
go.

Scope of this iteration is intentionally limited to **Mission** and **Tech
Stack**. Broader principles, governance, and roadmap are deferred to a later
iteration.

---

## Mission

### What ACA is for

ACA helps its author make their own short-form writing — tweets, blog posts, and
short articles — **more interesting for readers** by suggesting apt pop-culture
**citations** to weave in. Given a snippet of text, ACA surfaces a small set of
relevant, real, correctly-attributed quotes and references drawn from
pop-culture sources, and lets the author choose which (if any) to use.

### Who it serves

ACA is a **personal, single-user tool**. Its user is its author. There is no
audience of external customers, no multi-tenancy, no public product. Every design
decision optimizes for *one person enriching their own writing*, not for serving
many users.

### Why it matters

When writing, the author often senses that "there's a perfect quote or reference
for this" but can't recall it, or isn't sure of its exact wording or source. ACA
closes that gap: it does the remembering and the attribution, so a half-formed
intuition becomes a concrete, citable reference the author can drop into the
text.

### What success looks like

ACA is doing its job when, for a given snippet, it returns:

1. **Multiple candidate citations** the author can choose among — ACA proposes,
   the human selects. It is not expected to pick a single "right" answer.
2. **Correct attribution** — every suggested citation is a *real* quote/reference
   with an accurate source and author. Fabricated or misattributed citations are
   the primary failure mode to avoid; trustworthy provenance outranks volume or
   cleverness of matches.

### Non-goals

ACA is **not** a fact-checker, a plagiarism detector, a general web search
engine, or a multi-user/public service — it only proposes attributed pop-culture
citations for one author's own text.

---

## Tech Stack

Each choice below is stated as a **constraint with rationale**. Choices not yet
settled are explicitly marked **provisional / to-be-decided (TBD)** rather than
presented as committed.

### Language — Python (version-pinned) · *settled*

ACA is written in **Python, pinned to a minimum version of 3.11+**.
- *Rationale:* matches the surrounding monorepo's AI/agent tooling and ecosystem
  (LangChain/LangGraph, Anthropic SDK, vector-store clients), keeping ACA
  consistent with its neighbors. Pinning a modern minimum version guarantees
  access to current typing and standard-library features and keeps behavior
  reproducible across runs.

### LLM provider — Claude, behind a provider abstraction · *default settled, specific model provisional*

ACA uses an **LLM for its core reasoning** — semantic retrieval/ranking of
candidate citations, query reframing, and generating short explanations of why a
citation fits. The default provider is **Anthropic Claude** (a current Claude
model), but all model access goes **through a thin provider abstraction** so the
provider can be swapped without touching pipeline logic.
- *Rationale:* Claude offers strong multilingual (incl. Russian) understanding
  and reasoning, and matches existing tooling. The abstraction hedges against
  provider lock-in and lets cost/quality trade-offs change later.
- **Provisional:** the exact Claude model (and whether a cheaper model suffices
  for ranking vs. explanation) is **TBD** and may be tuned per pipeline step.

### Retrieval & storage — simple store + LLM ranking (Phase 1) · *settled for Phase 1*

For the **first phase, ACA does NOT use vector embeddings.** The citation corpus
lives in a **simple local store (SQLite or JSON)**, and **semantic matching is
performed by LLM call(s)** — optionally after a cheap keyword/full-text prefilter
to shortlist candidates.
- *Rationale:* at personal scale (one author, a bounded corpus) the simplest
  thing that can possibly work is a plain store plus an LLM that reasons over
  candidates. This avoids the cost, complexity, and quality-tuning burden of an
  embedding pipeline before it's proven necessary.

### Vector store & embeddings — Chroma + real multilingual embeddings · *future / provisional*

A later phase **may** introduce embedding-based retrieval once the corpus grows
or LLM-only ranking proves too slow/costly. The **intended** target is
**Chroma** as the vector store, paired with a **real, Russian-capable
(multilingual) embedding model**.
- *Rationale:* Chroma is a lightweight, local, persistent vector DB well-matched
  to a single-user tool; deferring it keeps Phase 1 simple while naming a clear
  upgrade path.
- **Provisional / TBD:** whether embeddings are adopted at all; the specific
  embedding model/provider (e.g. a hosted multilingual API vs. a local
  sentence-transformer); and whether Chroma remains the choice at that point.

### Sources — Russian pop-culture corpora · *settled (set), individual ingestion provisional*

ACA targets **Russian-language pop-culture sources**, beginning with:
- **Russian WikiQuote** (and similar quote databases) — films, books, notable
  people;
- **Russian meme / internet-culture sources** (e.g. Lurkmore, knowyourmeme-style
  wikis) — catchphrases and references.
- *Rationale:* ACA is **Russian-first**; these sources cover the quotes and
  references most relevant to the author's writing. Source ingestion must
  preserve enough metadata (text, author/work, source URL) to guarantee the
  correct-attribution mission requirement.
- **Provisional / TBD:** the concrete scraping/ingestion mechanism per source,
  and any additional sources (film/TV/lyrics) beyond the two above.

### Language scope — Russian-first · *settled*

ACA is **Russian-first**: input text, the citation corpus, and the surfaced
citations are primarily Russian.
- *Rationale:* the author writes in Russian and wants Russian pop-culture
  references. Other languages are **out of scope** for now, though nothing should
  be hard-coded in a way that forecloses adding them later.

### Observability — lightweight structured logging · *settled*

ACA uses **lightweight structured logging** (to stdout and/or a local file) of
each pipeline step (inputs, shortlisted candidates, LLM calls, chosen citations).
**No hosted tracing service** is required.
- *Rationale:* for a personal, locally-run tool, plain logs give enough
  visibility to debug and tune without the overhead or external dependency of a
  tracing platform.

### Runtime & deployment — local script, invoked from a Claude Code skill · *settled*

ACA runs as a **local script on the author's machine**, designed to be **invoked
from a Claude Code skill**. There is no hosting, no network service, no
authentication, and no multi-user concern.
- *Rationale:* matches the single-user mission and keeps operational complexity at
  zero. The script's interface (inputs/outputs) should be clean enough for a
  Claude Code skill to call it and present the candidate citations back to the
  author for selection.
