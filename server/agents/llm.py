from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from dotenv import load_dotenv
from tavily import TavilyClient
import re
import os


from .prompt import SYSTEM_PROMPT
from .tools import build_retriever_tool, search_web, write_report

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

model = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    max_tokens=1024,
    api_key=os.getenv("GROQ_API_KEY"),
)

def create_rag_agent(vector_store, session_name):
    retriever_tool = build_retriever_tool(vector_store, session_name)
    agent = create_agent(
        model=model,
        tools=[retriever_tool, search_web, write_report],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver()
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

    for msg in reversed(response["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content

    return "No response from AI"