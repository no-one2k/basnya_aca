"""
Citation search: reframe queries, search Chroma, generate explanations.
"""

import hashlib

from anthropic import Anthropic
from langsmith.wrappers import wrap_anthropic
import chromadb

from prompts import REFRAME_QUERIES_TOOL, REFRAME_QUERIES_PROMPT, GENERATE_EXPLANATION_TOOL, GENERATE_EXPLANATION_PROMPT


class CitationSearcher:
    """Core search functionality for retrieving and formatting citations."""

    def __init__(self, chroma_path: str = "./chroma_db"):
        """Initialize searcher with Chroma DB."""
        self.chroma_path = chroma_path
        # Initialize Chroma with persistent storage (new API)
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = None
        self.anthropic_client = wrap_anthropic(Anthropic())

    def load_collection(self, collection_name: str = "wikiquote_citations") -> None:
        """Load existing Chroma collection."""
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception as e:
            print(f"Error loading collection: {e}")
            raise

    def reframe_to_queries(self, user_text: str) -> list[str]:
        """Transform user text into 1-3 search queries using structured output."""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                tools=[REFRAME_QUERIES_TOOL],
                tool_choice={"type": "tool", "name": "generate_search_queries"},
                messages=[{
                    "role": "user",
                    "content": REFRAME_QUERIES_PROMPT.format(user_text=user_text)
                }]
            )

            # Parse structured output from tool use
            tool_use = response.content[0]
            queries = tool_use.input.get("queries", [])
            return queries[:3]  # Max 3 queries

        except Exception as e:
            print(f"Error reframing queries: {e}")
            return [user_text]  # Fallback to original

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text (matching indexing method)."""
        # Must match the embedding method used in indexing
        import random

        h = hashlib.md5(text.encode()).hexdigest()
        seed = int(h[:8], 16)
        rng = random.Random(seed)

        # Create 1536-dim vector matching indexing method
        embedding = [rng.gauss(0, 1) for _ in range(1536)]
        return embedding

    def search_citations(
        self,
        queries: list[str],
        k: int = 5,
        threshold: float = 0.0  # Simplified for prototype
    ) -> list[dict]:
        """Search Chroma for similar quotes and return top-K results."""
        if not self.collection:
            raise ValueError("Collection not loaded. Call load_collection() first.")

        all_results = []

        for query in queries:
            try:
                # Generate embedding for query
                query_embedding = self.generate_embedding(query)

                # Search Chroma using similarity
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k,
                    include=["documents", "metadatas", "distances"]
                )

                # Process results
                if results and results["documents"] and len(results["documents"]) > 0:
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        distance = results["distances"][0][i] if results["distances"] else 0

                        # Convert distance to similarity score (lower distance = higher similarity)
                        # For Chroma, normalize using simple heuristic
                        similarity = max(0, 1 - distance / 2.0)

                        result = {
                            "quote": doc,
                            "author": metadata.get("author", "Unknown"),
                            "source_url": metadata.get("source_url", ""),
                            "similarity_score": similarity,
                            "query": query
                        }
                        all_results.append(result)

            except Exception as e:
                print(f"Error searching query '{query}': {e}")

        # Sort by similarity and return top K
        all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return all_results[:k]

    def generate_explanation(self, quote: str, user_text: str) -> str:
        """Generate explanation of why quote is relevant to user text using structured output."""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=150,
                tools=[GENERATE_EXPLANATION_TOOL],
                tool_choice={"type": "tool", "name": "generate_explanation"},
                messages=[{
                    "role": "user",
                    "content": GENERATE_EXPLANATION_PROMPT.format(user_text=user_text, quote=quote)
                }]
            )

            # Parse structured output from tool use
            tool_use = response.content[0]
            explanation = tool_use.input.get("explanation", "")
            return explanation

        except Exception as e:
            print(f"Error generating explanation: {e}")
            return ""

    def format_citation(self, result: dict, user_text: str) -> dict:
        """Format a citation result as structured JSON."""
        explanation = self.generate_explanation(result["quote"], user_text)

        return {
            "quote": result["quote"],
            "author": result["author"],
            "source_url": result["source_url"],
            "explanation": explanation,
            "similarity_score": result["similarity_score"],
            "augmented_text": f'{user_text}\n\n[Citation: "{result["quote"]}" - {result["author"]}]'
        }

    def augment_text(self, user_text: str, citations: list[dict]) -> str:
        """Generate augmented text with numbered citation references."""
        if not citations:
            return user_text

        augmented = user_text + "\n\nRelated citations:\n"
        for i, citation in enumerate(citations, 1):
            augmented += f"\n[{i}] \"{citation['quote']}\" - {citation['author']}\n"
            augmented += f"    Source: {citation['source_url']}\n"

        return augmented


class SearchAgent:
    """Agentic orchestration of the search pipeline."""

    def __init__(self, chroma_path: str = "./chroma_db"):
        """Initialize the search agent."""
        self.searcher = CitationSearcher(chroma_path)
        self.searcher.load_collection()

    def run(self, user_text: str, k: int = 5) -> dict:
        """Execute search pipeline: reframe → search → explain → format."""
        result = {
            "status": "started",
            "user_text": user_text,
            "citations": [],
            "augmented_text": ""
        }

        try:
            # Step 1: Reframe to queries
            print("Step 1: Reframing text to search queries...")
            queries = self.searcher.reframe_to_queries(user_text)
            print(f"  Generated {len(queries)} queries: {queries}")
            result["queries"] = queries

            # Step 2: Search for citations
            print("Step 2: Searching for similar citations...")
            search_results = self.searcher.search_citations(queries, k=k)
            print(f"  Found {len(search_results)} results")
            result["raw_results_count"] = len(search_results)

            # Step 3: Format citations with explanations
            print("Step 3: Formatting citations...")
            formatted_citations = []
            for search_result in search_results:
                citation = self.searcher.format_citation(search_result, user_text)
                formatted_citations.append(citation)

            result["citations"] = formatted_citations
            result["citations_count"] = len(formatted_citations)

            # Step 4: Generate augmented text
            print("Step 4: Generating augmented text...")
            augmented = self.searcher.augment_text(user_text, formatted_citations)
            result["augmented_text"] = augmented

            result["status"] = "completed"
            print("Search complete!")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"Fatal error: {e}")

        return result
