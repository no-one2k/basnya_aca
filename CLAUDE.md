# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a monorepo containing experimental projects using a **spec-driven development workflow** powered by OpenSpec. The primary project is **basnya_aca** (Agent for Citation Augmentation), an agentic RAG-like tool that augments text snippets with citations and references from pop-culture sources.

**Key characteristics:**
- Experimental workflow using OpenSpec for spec-driven development
- Multiple custom Claude Code skills and commands in `.claude/` directory
- Python-based project using Claude Agent SDK and LangSmith integration
- Early-stage development with git history only in `basnya_aca/`

## Architecture

### Main Components

**basnya_aca** - Agent for Citation Augmentation:
1. **Index step**: Source pages (wikiquote, knowyourmeme, lurkmore) are split into individual quotes, expanded via query expansion, and embedded into a vector store
2. **Search step**: The agent reframes user text to search queries, retrieves top-K matches from the vector store, and returns citations with sources and explanations
3. **Target languages**: English and Russian

**Tech Stack:**
- Claude Agent SDK (`claude_agent_sdk`) - for building agentic workflows
- LangSmith - for tracing and monitoring agent execution
- OpenSpec - spec-driven development workflow

### Directory Structure

- `basnya_aca/` - Main project directory (contains its own git repo)
  - `.env` - Environment variables (LangSmith, Anthropic API keys) - **do not commit**
  - `trash/` - Experimental code and prototypes
- `openspec/` - OpenSpec configuration and workflow artifacts
  - `config.yaml` - Project context and rules
  - `changes/` - Completed spec changes
  - `specs/` - Specification templates
- `.claude/` - Custom Claude Code extensions
  - `commands/` - User-invocable commands (workflow, documentation, task management)
  - `skills/` - Skill definitions (OpenSpec operations, documentation, task automation)
  - `skills/openspec-*` - Skill definitions for OpenSpec operations
- `docs/basnya_aca/` - Project documentation
- `task_tracker/` - Task tracking for meta-work (skills, documentation)

## Development Workflow

This repository uses an **experimental spec-driven workflow** with OpenSpec. The primary entry points are the `/opsx` commands:

### Core Commands

- `/opsx:propose` - Propose a new change with design, specs, and implementation tasks
  - Use when starting a new feature or epic
  - Generates all artifacts in one step

- `/opsx:explore` - Explore mode for thinking through ideas and clarifying requirements
  - Use before proposing to investigate problems or design solutions
  - Good for understanding domain constraints

- `/opsx:apply` - Implement tasks from an OpenSpec change
  - Use to start or continue implementation of proposed tasks
  - Tracks progress through implementation phases

- `/opsx:archive` - Archive a completed change
  - Use after implementation is complete to finalize the change

### Workflow Example

1. Start exploring the problem space: `/opsx:explore`
2. Propose a solution: `/opsx:propose` (generates design document, specifications, and implementation tasks)
3. Implement: `/opsx:apply` (work through generated tasks)
4. Archive: `/opsx:archive` (finalize the completed work)

The OpenSpec configuration is in `openspec/config.yaml`. Generated artifacts are stored in `openspec/changes/` and `openspec/specs/`.

## Python Environment

**Setup:**
```bash
cd basnya_aca
pip install -r requirements.txt  # if available
# or install key dependencies:
pip install claude-agent-sdk anthropic langsmith python-dotenv
```

**Environment Variables** (in `basnya_aca/.env`):
- `ANTHROPIC_API_KEY` - Claude API key
- `LANGSMITH_ENDPOINT` - LangSmith tracing endpoint
- `LANGSMITH_API_KEY` - LangSmith API key
- `LANGSMITH_PROJECT` - LangSmith project name

**Do NOT commit `.env` file** - it contains secrets. The `.gitignore` is properly configured to exclude it.

## Testing & Running Code

The test file in `basnya_aca/trash/test_langsmith_anthropic.py` demonstrates:
- Setting up a Claude Agent SDK client with a custom MCP server (weather)
- Integrating with LangSmith for tracing
- Basic agentic interaction pattern

**To run the example:**
```bash
cd basnya_aca
python trash/test_langsmith_anthropic.py
```

## Task Tracking

Meta-tasks (skills to create, documentation to update) are tracked in `task_tracker/tracker.md`. Update this file as high-level tasks are completed.

## Key Concepts

### OpenSpec Workflow
OpenSpec enables specification-driven development by:
- Starting with clear problem statements and design proposals
- Generating formal specifications that guide implementation
- Breaking work into tracked, implementable tasks
- Maintaining an audit trail of changes and decisions

### Claude Agent SDK
Used for building multi-step agentic workflows with:
- Tool/function calling capabilities
- MCP (Model Context Protocol) server integration
- Async execution patterns

### LangSmith Integration
Provides observability into agent behavior:
- Traces all agent decisions and tool calls
- Project-based organization of runs
- Integration with Claude Agent SDK via `configure_claude_agent_sdk()`
