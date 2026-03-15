"""
Prompts and tool schemas for structured LLM output in the ACA prototype.
"""

# Tool schemas for Anthropic structured output (used with tool_choice)
EXPAND_QUOTE_TOOL = {
    "name": "classify_and_expand_quote",
    "description": "Classify a quote's fame level and optionally expand it with variations",
    "input_schema": {
        "type": "object",
        "properties": {
            "fame_level": {
                "type": "string",
                "enum": ["very_famous", "famous", "less_known", "unknown"],
                "description": "How famous/recognizable this quote is in popular culture"
            },
            "variations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Alternative phrasings for search (empty for short/unknown quotes)"
            }
        },
        "required": ["fame_level", "variations"]
    }
}

REFRAME_QUERIES_TOOL = {
    "name": "generate_search_queries",
    "description": "Generate search queries from user text",
    "input_schema": {
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "1-3 search queries"
            }
        },
        "required": ["queries"]
    }
}

GENERATE_EXPLANATION_TOOL = {
    "name": "generate_explanation",
    "description": "Explain why a quote is relevant to user text",
    "input_schema": {
        "type": "object",
        "properties": {
            "explanation": {
                "type": "string",
                "description": "1-2 sentence explanation of relevance"
            }
        },
        "required": ["explanation"]
    }
}

# Prompt templates
EXPAND_QUOTE_PROMPT = """Classify this quote by how famous/recognizable it is in popular culture (very_famous, famous, less_known, or unknown).

For quotes that are "famous" or "very_famous" AND are long (over 100 characters), also provide 2-3 alternative phrasings that capture the semantic meaning for search purposes.
For short quotes (under 100 characters) or less_known/unknown quotes, return an empty variations list.

Quote: {quote_text}"""

REFRAME_QUERIES_PROMPT = """Generate 1-3 search queries that capture the semantic intent of this text for finding relevant citations.

Text: {user_text}"""

GENERATE_EXPLANATION_PROMPT = """Explain in 1-2 sentences why this quote is relevant to the user's text.

User text: {user_text}
Quote: {quote}"""
