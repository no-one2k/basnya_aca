"""
LangSmith tracing configuration for ACA agents.
Enables observability into agent decisions and tool calls.
"""

import os
from langsmith import Client


def configure_langsmith_tracing():
    """Configure LangSmith tracing for ACA agents."""
    # Initialize LangSmith client
    # Credentials read from environment variables:
    # - LANGSMITH_API_KEY
    # - LANGSMITH_ENDPOINT
    # - LANGSMITH_PROJECT

    api_key = os.getenv("LANGSMITH_API_KEY")
    endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    project = os.getenv("LANGSMITH_PROJECT", "basnya_aca")

    if not api_key:
        print("Warning: LANGSMITH_API_KEY not set. LangSmith tracing disabled.")
        return None

    try:
        client = Client(
            api_key=api_key,
            endpoint=endpoint,
        )
        print(f"✓ LangSmith tracing configured for project: {project}")
        return client
    except Exception as e:
        print(f"Warning: Failed to configure LangSmith: {e}")
        return None


def trace_agent_run(agent_name: str, run_data: dict, client=None):
    """Log agent run to LangSmith."""
    if not client:
        return

    try:
        # Create a run entry for this agent execution
        project = os.getenv("LANGSMITH_PROJECT", "aca-prototype")

        run = client.create_run(
            name=f"{agent_name}_run",
            run_type="agent",
            project_name=project,
            inputs={"data": run_data},
        )

        # Log completion
        client.update_run(
            run.id,
            end_time=run.end_time,
            outputs={"result": run_data},
        )

        print(f"  ✓ Traced {agent_name} run to LangSmith")

    except Exception as e:
        print(f"  Warning: Failed to trace to LangSmith: {e}")
