"""
ACA Prototype - Main entry point for indexing and search.
Supports two modes: index and search.
"""

import argparse
import sys
from pathlib import Path

from indexing import IndexingAgent
from search import SearchAgent


def run_index(urls_file, db_path="chroma_db"):
    """Run indexing mode."""
    print("=" * 60)
    print("Agent for Citation Augmentation (ACA) - Indexing")
    print("=" * 60)

    urls_file = Path(urls_file)
    if not urls_file.exists():
        print(f"❌ Error: {urls_file} not found")
        return False

    print(f"\n📚 Indexing URLs from: {urls_file}")
    print(f"📂 Database path: {db_path}")
    print("-" * 60)

    try:
        indexing_agent = IndexingAgent(db_path)
        result = indexing_agent.run(str(urls_file))

        print(f"\n✓ Indexing Result:")
        print(f"  - Status: {result['status']}")
        print(f"  - URLs found: {result.get('urls_found', 0)}")
        print(f"  - URLs processed: {result.get('urls_processed', 0)}")
        print(f"  - Quotes scraped: {result.get('quotes_scraped', 0)}")
        print(f"  - Quotes expanded: {result.get('quotes_expanded', 0)}")
        print(f"  - Quotes stored: {result.get('quotes_stored', 0)}")

        if result.get('errors'):
            print(f"  - Errors: {len(result['errors'])}")
            for error in result['errors'][:3]:
                print(f"    • {error}")

        success = result['status'] == 'completed'
        if success:
            print("\n✓ Indexing completed successfully")
        else:
            print("\n❌ Indexing failed")
        return success

    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_search(query, db_path="chroma_db", k=3):
    """Run search mode."""
    print("=" * 60)
    print("Agent for Citation Augmentation (ACA) - Search")
    print("=" * 60)

    print(f"\n📝 Query: {query}")
    print(f"📂 Database path: {db_path}")
    print("-" * 60)

    try:
        search_agent = SearchAgent(db_path)
        result = search_agent.run(query, k=k)

        if result['status'] == 'completed':
            citations_count = result.get('citations_count', 0)
            print(f"\n✓ Found {citations_count} citations")

            for i, citation in enumerate(result.get('citations', []), 1):
                print(f"\n  [{i}] \"{citation['quote'][:80]}...\"")
                print(f"      - Author: {citation['author']}")
                print(f"      - Similarity: {citation['similarity_score']:.2f}")
                if citation.get('explanation'):
                    print(f"      - Why: {citation['explanation'][:100]}...")
            return True
        else:
            print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Parse arguments and run appropriate mode."""
    parser = argparse.ArgumentParser(
        description="ACA Prototype - Index WikiQuote citations or search for related quotes"
    )
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')

    # Index mode
    index_parser = subparsers.add_parser('index', help='Index URLs from a CSV file')
    index_parser.add_argument('urls_file', help='Path to CSV file with WikiQuote URLs')
    index_parser.add_argument('--db', default='chroma_db', help='Chroma database path (default: chroma_db)')

    # Search mode
    search_parser = subparsers.add_parser('search', help='Search for related quotes')
    search_parser.add_argument('query', help='Query sentence to find related quotes')
    search_parser.add_argument('--db', default='chroma_db', help='Chroma database path (default: chroma_db)')
    search_parser.add_argument('--k', type=int, default=3, help='Number of results to return (default: 3)')

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        return

    if args.mode == 'index':
        success = run_index(args.urls_file, args.db)
        sys.exit(0 if success else 1)
    elif args.mode == 'search':
        success = run_search(args.query, args.db, args.k)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
