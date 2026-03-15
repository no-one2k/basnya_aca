import os
from pathlib import Path

from dotenv import load_dotenv
env_file = Path(__file__).parent.parent.joinpath('.env')
load_dotenv(env_file)
# for k, v in os.environ.items():
#     if "lang" in k.lower():
#         print(f"{k}: {v}")


import asyncio
from asyncio import sleep
from typing import Any

from langsmith import Client, traceable



ls_client = Client(
    api_url=os.getenv("LANGSMITH_ENDPOINT"),
    api_key=os.getenv("LANGSMITH_API_KEY"),
)

projects = list(ls_client.list_projects())
print(projects)

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    create_sdk_mcp_server,
    tool,
)
from langsmith.integrations.claude_agent_sdk import configure_claude_agent_sdk

configure_claude_agent_sdk(project_name=os.getenv("LANGSMITH_PROJECT"))


@tool(
    "get_weather",
    "Gets the current weather for a given city",
    {"city": str},
)
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    city = args["city"]
    weather_data = {
        "San Francisco": "Foggy, 62°F",
        "New York": "Sunny, 75°F",
        "London": "Rainy, 55°F",
        "Tokyo": "Clear, 68°F",
    }
    weather = weather_data.get(city, "Weather data not available")
    return {"content": [{"type": "text", "text": f"Weather in {city}: {weather}"}]}

@traceable
async def main(prompt):
    weather_server = create_sdk_mcp_server(
        name="weather",
        version="1.0.0",
        tools=[get_weather],
    )

    options = ClaudeAgentOptions(
        model="claude-haiku-4-5-20251001",
        system_prompt=prompt,
        mcp_servers={"weather": weather_server},
        allowed_tools=["mcp__weather__get_weather"],
    )
    result = None
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What's the weather like in San Francisco and Tokyo?")

        async for message in client.receive_response():
            print(message)
            result = message
    await sleep(5)
    return result


if __name__ == "__main__":
    asyncio.run(main("You are a friendly travel assistant who helps with weather information."))