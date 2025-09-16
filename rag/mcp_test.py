import os
from dotenv import load_dotenv
from langchain_mcp_adapters.tools import MAX_ITERATIONS, load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent

from typing import TypedDict, Dict, Any

import asyncio
import json

from langchain_core.tools import BaseTool, tool
from langchain_core.messages import HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START, END

from pprint import pprint

from openai import max_retries
from requests import session

load_dotenv()

MODEL_NAME = "mistralai/mistral-small-3.1-24b-instruct"

llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_API_URL"),
)

mcp_config = {
    "supabase": {
        "command": "npx",
        "args": [
            "-y",
            "@supabase/mcp-server-supabase@latest",
            "--access-token",
            os.getenv("SUPABASE_TOKEN_MCP"),
            "--features=database",  # вот сюда добавляем
        ],
        "transport": "stdio",
    },
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "./File_system_test"],
        "transport": "stdio",
    },
    "exa": {
        "command": "npx",
        "args": ["-y", "exa-mcp-server", "--tools=web_search"],
        "env": {
            "EXA_API_KEY": os.getenv("EXA_SEARCH_MCP"),
        },
        "transport": "stdio",
    },
}


client = MultiServerMCPClient(mcp_config)

servers_names = list(mcp_config.keys())
max_iterations = 3
recursion_limit = 2 * max_iterations + 1


async def get_tools():
    tools = await client.get_tools()

    print(f"всего инструментов {len(tools)}")

    # for server in servers_names:
    #     tools = await client.get_tools(server_name=server)
    #     print(f"\nНайдено {len(tools ) } инструментов от {server}")

    # for tool in tools:
    #     pprint(tool.name)
    #     pprint(tool.description)

    return tools


tools = asyncio.run(get_tools())


# pprint(tool.tool_call_schema)


agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt="""Ты ассистент, который может работать с базой данных Supabase. И файловой системой.
    Используй инструменты, чтобы получать данные из бд и затем работать с файловой системой.
    id проекта = wpwnkbgmqxewlwjnimlw
    папка для сохранения файлов = D:\Repos\AI Agent\File_system_test""",
)


async def main():
    await get_tools()
    try:
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Получи то, что тебе вернет инструмент list_tables в сыром виде и сохрани в файл",
                    }
                ],
            },
            {"recursion_limit": recursion_limit},
        )
        print(result["messages"][-1].content)
    except GraphRecursionError:
        print("Ошибка. Превышено количество итераций")

    # response = await llm.ainvoke("Привет, ты кто?")
    # pprint(response.content)


asyncio.run(main())
