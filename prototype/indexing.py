"""
WikiQuote indexing pipeline: scrape quotes, expand, embed, and store in Chroma.
"""

import json
import os
import re
import hashlib

import requests
from anthropic import Anthropic
from langsmith.wrappers import wrap_anthropic
import chromadb

from prompts import EXPAND_QUOTE_TOOL, EXPAND_QUOTE_PROMPT


class WikiQuoteIndexer:
    """Core indexing functionality for WikiQuote citations."""

    def __init__(self, chroma_path: str = "./chroma_db", cache_dir: str = "./scrape_cache"):
        """Initialize indexer with Chroma DB and optional caching."""
        self.chroma_path = chroma_path
        self.cache_dir = cache_dir
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        # Initialize Chroma with persistent storage (new API)
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = None
        self.anthropic_client = wrap_anthropic(Anthropic())

    def init_collection(self, collection_name: str = "wikiquote_citations") -> None:
        """Initialize or get Chroma collection."""
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"source": "wikiquote", "language": "en"}
        )

    def read_urls_from_file(self, file_path: str) -> list[str]:
        """Parse WikiQuote URLs from file (one per line, CSV, or JSON format)."""
        urls = []
        with open(file_path, 'r') as f:
            content = f.read().strip()

        # Try JSON array format first
        try:
            data = json.loads(content)
            if isinstance(data, list):
                urls = [url.strip() for url in data if isinstance(url, str)]
            return urls
        except (json.JSONDecodeError, ValueError):
            pass

        # Try CSV format (extract URLs from any column)
        if ',' in content.split('\n')[0]:
            for line in content.split('\n'):
                if line.strip():
                    # Extract first URL-like field
                    fields = [f.strip() for f in line.split(',')]
                    for field in fields:
                        if 'wikiquote' in field.lower():
                            urls.append(field)
                            break
        else:
            # Plain text, one URL per line
            urls = [line.strip() for line in content.split('\n') if line.strip()]

        return urls

    def scrape_wikiquote_page(self, url: str) -> list[dict]:
        """Fetch and parse quotes from a WikiQuote page (with caching)."""
        # Check cache first
        cache_key = hashlib.md5(url.encode()).hexdigest()[:12]
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading cache for {url}: {e}")

        quotes = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.4.2; en-US; HTC One Build/KOT49H) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Simple HTML parsing for quote blocks
            # Look for <dl> tags that typically contain quotes on WikiQuote
            html = response.text

            # Extract title/author from page
            title_match = re.search(r'<title>([^<]+)</title>', html)
            page_author = title_match.group(1).split('|')[0].strip() if title_match else "Unknown"

            # Find quote blocks (simplified parsing)
            # WikiQuote uses <dl><dd> for quotes
            dd_pattern = r'<dd[^>]*>(.*?)</dd>'
            for match in re.finditer(dd_pattern, html, re.DOTALL):
                quote_html = match.group(1)
                # Clean HTML tags
                quote_text = re.sub(r'<[^>]+>', '', quote_html).strip()
                quote_text = re.sub(r'\s+', ' ', quote_text)  # Normalize whitespace

                if quote_text and len(quote_text) > 20:  # Minimum length
                    quotes.append({
                        "text": quote_text,
                        "author": page_author,
                        "source_url": url,
                        "raw_html": quote_html[:200]  # Store some context
                    })

            # Save to cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump(quotes, f)
            except Exception as e:
                print(f"Error writing cache for {url}: {e}")

        except Exception as e:
            print(f"Error scraping {url}: {e}")

        return quotes

    def expand_quote(self, quote_text: str) -> dict:
        """Classify quote fame level and generate variations (with caching)."""
        # Check cache first
        cache_key = hashlib.md5(quote_text.encode()).hexdigest()[:12]
        cache_file = os.path.join(self.cache_dir, f"expand_{cache_key}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading expand cache: {e}")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                tools=[EXPAND_QUOTE_TOOL],
                tool_choice={"type": "tool", "name": "classify_and_expand_quote"},
                messages=[{
                    "role": "user",
                    "content": EXPAND_QUOTE_PROMPT.format(quote_text=quote_text)
                }]
            )

            # Parse structured output from tool use
            tool_use = response.content[0]
            result = {
                "fame_level": tool_use.input.get("fame_level", "unknown"),
                "variations": tool_use.input.get("variations", [])
            }

            # Save to cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump(result, f)
            except Exception as e:
                print(f"Error writing expand cache: {e}")

            return result

        except Exception as e:
            print(f"Error expanding quote: {e}")
            return {"fame_level": "unknown", "variations": []}

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text using Claude."""
        try:
            # Use a simple deterministic embedding for prototyping
            # In production, use real embeddings API
            import hashlib
            import random

            # Seed random with text hash for determinism
            h = hashlib.md5(text.encode()).hexdigest()
            seed = int(h[:8], 16)
            rng = random.Random(seed)

            # Create 1536-dim vector (OpenAI embedding size)
            embedding = [rng.gauss(0, 1) for _ in range(1536)]

            return embedding

        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * 1536

    def store_in_chroma(self, quotes: list[dict]) -> None:
        """Store quotes and embeddings in Chroma DB with fame metadata and variations."""
        if not self.collection:
            self.init_collection()

        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for quote in quotes:
            # Get quote expansion info (fame_level + variations)
            expansion = quote.get("expansion", {"fame_level": "unknown", "variations": []})
            fame_level = expansion.get("fame_level", "unknown")
            variations = expansion.get("variations", [])

            # Generate ID from quote text hash
            quote_id = hashlib.md5(
                f"{quote['text']}{quote.get('source_url', '')}".encode()
            ).hexdigest()[:12]

            # Store original quote
            embedding = self.generate_embedding(quote["text"])
            ids.append(quote_id)
            documents.append(quote["text"])
            embeddings.append(embedding)
            metadatas.append({
                "author": quote.get("author", "Unknown"),
                "source_url": quote.get("source_url", ""),
                "fame_level": fame_level,
            })

            # For famous/very_famous quotes, also store variations
            if fame_level in ["famous", "very_famous"] and variations:
                for j, variation in enumerate(variations):
                    var_id = f"{quote_id}_var_{j}"
                    var_embedding = self.generate_embedding(variation)
                    ids.append(var_id)
                    documents.append(variation)
                    embeddings.append(var_embedding)
                    metadatas.append({
                        "author": quote.get("author", "Unknown"),
                        "source_url": quote.get("source_url", ""),
                        "fame_level": fame_level,
                        "is_variation": True,
                        "original_id": quote_id,
                    })

        if ids:
            try:
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
                print(f"Stored {len(ids)} documents in Chroma DB (including variations)")
            except Exception as e:
                print(f"Error storing in Chroma: {e}")


class IndexingAgent:
    """Agentic orchestration of the indexing pipeline."""

    def __init__(self, chroma_path: str = "./chroma_db", cache_dir: str = "./scrape_cache"):
        """Initialize the indexing agent."""
        self.indexer = WikiQuoteIndexer(chroma_path, cache_dir)
        self.indexer.init_collection()

    def run(self, urls_file: str) -> dict:
        """Execute full indexing pipeline: parse URLs → scrape → expand → embed → store."""
        result = {
            "status": "started",
            "urls_processed": 0,
            "quotes_scraped": 0,
            "quotes_expanded": 0,
            "quotes_stored": 0,
            "errors": []
        }

        try:
            # Step 1: Parse URLs
            print("Step 1: Parsing URLs from file...")
            urls = self.indexer.read_urls_from_file(urls_file)
            print(f"  Found {len(urls)} URLs")
            result["urls_found"] = len(urls)

            all_quotes = []

            # Step 2: Scrape quotes from each URL
            print("Step 2: Scraping quotes from WikiQuote pages...")
            for url in urls:
                try:
                    quotes = self.indexer.scrape_wikiquote_page(url)
                    all_quotes.extend(quotes)
                    result["urls_processed"] += 1
                    result["quotes_scraped"] += len(quotes)
                    print(f"  Scraped {len(quotes)} quotes from {url}")
                except Exception as e:
                    result["errors"].append(f"Error scraping {url}: {str(e)}")
                    print(f"  Error: {e}")

            # Step 3: Expand quotes with fame classification
            print("Step 3: Expanding quotes with LLM classification...")
            expanded_quotes = []
            for quote in all_quotes:
                expansion = self.indexer.expand_quote(quote["text"])
                quote["expansion"] = expansion
                expanded_quotes.append(quote)
                result["quotes_expanded"] += 1

            # Step 4: Store in Chroma DB
            print("Step 4: Storing quotes in Chroma DB...")
            self.indexer.store_in_chroma(expanded_quotes)
            result["quotes_stored"] = len(expanded_quotes)

            result["status"] = "completed"
            print("Indexing complete!")

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            print(f"Fatal error: {e}")

        return result
