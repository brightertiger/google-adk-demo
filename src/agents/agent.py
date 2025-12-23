import os
import json
import yaml
import logging
import asyncio
import uuid
import litellm
from json_repair import repair_json
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

litellm.suppress_debug_info = True
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

MODEL = "gemini/gemini-2.0-flash"
APP_NAME = "adk_agent"


async def get_tools_async(path_to_mcp_server: str):
    logger.info("Attempting to connect to MCP Filesystem server...")
    toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python", args=[path_to_mcp_server]
            )
        )
    )
    tools = await toolset.get_tools()
    logger.info("MCP Toolset created successfully.")
    return tools, toolset


async def get_specialist_agent(config: dict, tools: list):
    agent = Agent(
        model=LiteLlm(
            model=MODEL,
            api_key=os.getenv("GOOGLE_API_KEY"),
            generate_content_config=types.GenerateContentConfig(
                temperature=0.1,
            ),
        ),
        name=config["name"],
        description=config["description"],
        instruction=config["instruction"],
        tools=tools if config["use_tools"] else [],
        output_key=config["output_key"],
    )
    logger.info(f"Agent {agent.name} created successfully.")
    return agent


async def get_manager_agent(config: dict, tools: list):
    crawler_agent = await get_specialist_agent(config["crawler_agent"], tools)
    address_agent = await get_specialist_agent(config["address_agent"], [])
    geocoding_agent = await get_specialist_agent(config["geocoding_agent"], tools)
    manager_agent = Agent(
        model=LiteLlm(
            model=MODEL,
            api_key=os.getenv("GOOGLE_API_KEY"),
            generate_content_config=types.GenerateContentConfig(
                temperature=0.1,
            ),
        ),
        name="manager_agent",
        description=config["manager_agent"]["description"],
        instruction=config["manager_agent"]["instruction"],
        tools=tools,
        sub_agents=[crawler_agent, address_agent, geocoding_agent],
    )
    logger.info(f"Manager agent {manager_agent.name} created successfully.")
    return manager_agent


async def get_sequential_agent(config: dict, tools: list):
    crawler_agent = await get_specialist_agent(config["crawler_agent"], tools)
    address_agent = await get_specialist_agent(config["address_agent"], [])
    geocoding_agent = await get_specialist_agent(config["geocoding_agent"], tools)
    agent = SequentialAgent(
        name=config["sequential_agent"]["name"],
        sub_agents=[crawler_agent, address_agent, geocoding_agent],
    )
    logger.info(f"Sequential agent {agent.name} created successfully.")
    return agent


async def call_agent_async(query: str, user_id: str, session_id: str, runner: Runner):
    content = types.Content(role="user", parts=[types.Part(text=query)])
    final_response_text = None
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        logger.info(
            f"[Event] Author: {event.author}, Type: {type(event).__name__}, Content: {event.content}, "
        )
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = (
                    f"Agent escalated: {event.error_message or 'No specific message.'}"
                )
            break
    if final_response_text is None:
        raise RuntimeError("No final response received from the agent")
    return final_response_text


async def main(config: dict, query: str, user_id: str, session_id: str):
    tools, toolset = await get_tools_async(
        path_to_mcp_server=config["mcp_server"]["path"]
    )
    agent = await get_manager_agent(config, tools)
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    output = await call_agent_async(
        query=query,
        user_id=user_id,
        session_id=session_id,
        runner=runner,
    )
    output = repair_json(output)
    output = json.loads(output)
    try:
        logger.info("Output: %s", json.dumps(output, indent=4))
        json.dump(output, open("output.json", "w"), indent=4)
    finally:
        await toolset.close()


if __name__ == "__main__":
    with open("src/agents/config.yaml", "r") as f:
        config = yaml.safe_load(f)
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    load_dotenv(".env")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
    query = config["query"]
    query_url = "https://tattvammedia.com/blog/list-of-google-offices-in-india/"
    query = query.replace("{{query_url}}", query_url)
    asyncio.run(main(config, query, user_id, session_id))
