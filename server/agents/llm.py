from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents import create_agent
from langchain.tools import tool
from dotenv import load_dotenv
from tavily import TavilyClient
import sqlite3
import re
import os

from .prompt import SYSTEM_PROMPT

load_dotenv()
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

model = ChatOpenRouter(
    model="google/gemini-2.5-flash",
    temperature=0,
    max_tokens=1024,
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
conn = sqlite3.connect(
    r"C:\Projects\Python-projects\ReviewBot\.reviewbot\database\memory.db",
    check_same_thread=False
)

memory = SqliteSaver(conn=conn)


@tool
def search_web(query: str):
    """This tool performs a web search with the given query."""
    return client.search(query)


def build_retriever_tool(vector_store):
    @tool
    def search_codebase(query: str) -> str:
        """
        Search the indexed codebase for relevant code snippets and files. 
        Always use this tool when the user asks about repository code.
        """
        match = re.search(r"\b[\w\-]+\.py\b", query)
        if match:
            filename = match.group(0)
            docs = vector_store.get(
                where={"path": {"$contains": filename}}
            )

            if docs and docs["documents"]:
                content = "\n\n".join(docs["documents"])
                return f"### Full file: {filename}\n```python\n{content}\n```"
        results = vector_store.similarity_search_with_score(query, k=5)
        formatted = []
        for doc, score in results:
            formatted.append(
                f"### File: {doc.metadata.get('path')}\n"
                f"Score: {score}\n"
                f"```python\n{doc.page_content}\n```"
            )
        return "\n\n".join(formatted)
    return search_codebase

def create_rag_agent(vector_store):
    retriever_tool = build_retriever_tool(vector_store)

    agent = create_agent(
        model=model,
        checkpointer=memory,
        tools=[retriever_tool, search_web],
        system_prompt=SYSTEM_PROMPT
    )

    return agent


async def generate_ai_response(agent, user_input: str, thread_id: str) -> str:

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    response = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config
    )

    return response["messages"][-1].content