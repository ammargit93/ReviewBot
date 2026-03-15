from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents import create_agent
from dotenv import load_dotenv
from tavily import TavilyClient
import sqlite3
import re
import os


from .prompt import SYSTEM_PROMPT
from .tools import build_retriever_tool, search_web, spawn_container

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

model = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=1024,
    api_key=os.getenv("GROQ_API_KEY"),
)

conn = sqlite3.connect(
    r"C:\Projects\Python-projects\ReviewBot\.reviewbot\database\memory.db",
    check_same_thread=False
)

memory = SqliteSaver(conn=conn)

def create_rag_agent(vector_store):
    retriever_tool = build_retriever_tool(vector_store)
    agent = create_agent(
        model=model,
        checkpointer=memory,
        tools=[retriever_tool, search_web, spawn_container],
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