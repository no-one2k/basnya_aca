# Agent for Citation Augmentation (ACA) - Prototype

A RAG-like system that augments text snippets with citations from pop-culture sources.

## Overview

ACA is an agentic workflow that performs two main operations:

1. **Indexing Phase**: Scrapes WikiQuote pages, extracts famous quotes, expands them semantically, generates embeddings, and stores them in a vector database (Chroma).
2. **Search Phase**: Takes user text, generates search queries, retrieves relevant citations from the vector database, and returns augmented text with explanations.

## Architecture

### Modules

- **`indexing.py`**: Core indexing logic
  - `WikiQuoteIndexer`: Handles scraping, filtering, expansion, embedding, and storage
  - `IndexingAgent`: Orchestrates the full indexing pipeline

- **`search.py`**: Core search logic
  - `CitationSearcher`: Handles query reframing, vector search, explanation generation, and output formatting
  - `SearchAgent`: Orchestrates the full search pipeline

- **`tracing.py`**: LangSmith integration for observability
- **`main.py`**: End-to-end demonstration script

## Setup

### Prerequisites

- Python 3.9+
- Environment variables:
  - `ANTHROPIC_API_KEY`: Your Claude API key
  - `LANGSMITH_API_KEY` (optional): For tracing
  - `LANGSMITH_ENDPOINT` (optional): LangSmith endpoint

### Installation

```bash
# Install dependencies
pip install chromadb anthropic langsmith requests python-dotenv

# Create .env file in basnya_aca/
echo "ANTHROPIC_API_KEY=your_key_here" > ../.env
```

## Usage

### Indexing WikiQuote Citations

```python
from indexing import IndexingAgent

# Initialize agent
agent = IndexingAgent(chroma_path="./chroma_db")

# Run indexing on WikiQuote URLs
result = agent.run("wikiquote_urls.csv")

# Result contains:
# - status: "completed" or "failed"
# - urls_processed, quotes_scraped, quotes_filtered, quotes_stored
# - errors: list of any errors encountered
```

### Searching for Citations

```python
from search import SearchAgent

# Initialize agent with existing Chroma DB
agent = SearchAgent(chroma_path="./chroma_db")

# Run search on user text
result = agent.run("Your text here", k=5)

# Result contains:
# - status: "completed" or "failed"
# - citations: list of formatted citations with explanations
# - augmented_text: original text with citations appended
```

### End-to-End Workflow

```bash
# Run the full demonstration
python main.py
```

## How It Works

### Indexing Pipeline

1. **Parse URLs**: Read WikiQuote URLs from CSV/JSON file
2. **Scrape Pages**: Fetch HTML from each WikiQuote page and extract quote blocks
3. **Filter Quotes**: Keep only short (< 500 chars), well-attributed quotes
4. **Expand Queries**: Use Claude to generate 2-3 semantic variations of each quote
5. **Generate Embeddings**: Create vector representations for similarity search
6. **Store in Chroma**: Persist quotes, metadata, and embeddings for retrieval

### Search Pipeline

1. **Reframe Queries**: Transform user text into 1-3 optimized search queries
2. **Vector Search**: Query Chroma DB for top-K semantically similar quotes
3. **Generate Explanations**: Use Claude to explain why each citation is relevant
4. **Format Output**: Return structured JSON citations with source URLs
5. **Augment Text**: Append numbered citation references to original text

## Data Format

### WikiQuote URLs File

Supports multiple formats:

**CSV:**
```csv
Movie,Year,WikiQuote URL
Gone with the Wind,1939,https://en.wikiquote.org/wiki/Gone_with_the_Wind
The Godfather,1972,https://en.wikiquote.org/wiki/The_Godfather
```

**Plain text (one URL per line):**
```
https://en.wikiquote.org/wiki/Gone_with_the_Wind
https://en.wikiquote.org/wiki/The_Godfather
```

**JSON:**
```json
[
  "https://en.wikiquote.org/wiki/Gone_with_the_Wind",
  "https://en.wikiquote.org/wiki/The_Godfather"
]
```

### Citation Output Format

```json
{
  "quote": "Here's looking at you, kid",
  "author": "Rick - Casablanca",
  "source_url": "https://en.wikiquote.org/wiki/Casablanca_(film)",
  "explanation": "This classic line expresses intimate farewell, similar to your farewell sentiment.",
  "similarity_score": 0.87,
  "augmented_text": "Your original text here\n\n[Citation: \"Here's looking at you, kid\" - Rick - Casablanca]"
}
```

## Limitations & Future Work

### Current Limitations (Prototype)

- **Language**: English only
- **Source**: WikiQuote only (knowyourmeme and lurkmore coming soon)
- **Scale**: Optimized for ~10k-100k quotes (Chroma not designed for massive scale)
- **Embeddings**: Deterministic hash-based embeddings for demo (real embeddings API needed for production)
- **Deduplication**: No cross-source deduplication (duplicate quotes stored separately)

### Future Phases

1. **Multi-source support**: Add knowyourmeme, lurkmore, and other pop-culture sources
2. **Multi-language**: Add Russian and other languages
3. **Production embeddings**: Use real embedding APIs for better semantic search
4. **Deduplication**: Implement fuzzy matching to detect and merge duplicate quotes
5. **Re-ranking**: Add BM25 or learning-to-rank for better citation quality
6. **Web API**: Deploy as REST service with authentication
7. **Feedback loop**: Collect user feedback to improve citation relevance

## Configuration

### Chroma Database

- **Path**: Customize with `chroma_path` parameter
- **Default**: `./chroma_db` (persistent storage using DuckDB)
- **Persistence**: Automatically persists between runs

### Similarity Threshold

- **Default**: 0.0 (return all results)
- **Recommended**: 0.7 or higher for production quality

### Top-K Results

- **Default**: 5
- **Customizable**: Pass `k` parameter to search methods

## Observability

### LangSmith Integration

If `LANGSMITH_API_KEY` is set, all agent runs are traced:

```python
from tracing import configure_langsmith_tracing, trace_agent_run

client = configure_langsmith_tracing()
# Agent runs are automatically traced if client is configured
```

### Logging

Agents provide detailed logging of each pipeline step:

- URLs found/processed
- Quotes scraped/filtered/stored
- Query reformulations
- Citation matches with similarity scores

## Troubleshooting

### Import Errors

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version is 3.9+

### Chroma DB Errors

- Delete `./chroma_db` directory and re-index if you encounter legacy format errors
- Use `PersistentClient` API (not deprecated `Settings` API)

### API Key Errors

- Set `ANTHROPIC_API_KEY` environment variable
- For testing without Claude API, set `ANTHROPIC_API_KEY=dummy` (mock requests will fail gracefully)

### Empty Search Results

- Verify indexing completed: check `quotes_stored` > 0
- Try broader search queries
- Increase `k` parameter to retrieve more results

## Contributing

This prototype is part of the `basnya_aca` project using OpenSpec workflow.

See `/openspec/changes/aca-prototype/` for design documents and specifications.

## License

Experimental prototype - Use for evaluation and development only.
