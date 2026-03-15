"""
Agent for Citation Augmentation (ACA) - Prototype
A RAG-like system that augments text with citations from pop-culture sources.
"""

from .indexing import IndexingAgent, WikiQuoteIndexer
from .search import SearchAgent, CitationSearcher

__all__ = [
    "IndexingAgent",
    "SearchAgent",
    "WikiQuoteIndexer",
    "CitationSearcher",
]
