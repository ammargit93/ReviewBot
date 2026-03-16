from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

from .tools import build_retriever_tool
from .prompt import SECURITY_AGENT_PROMPT

load_dotenv()

def create_security_agent(vector_store, model=None):

    if model is None:
        model = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0,
            max_tokens=1024,
            api_key=os.getenv("GROQ_API_KEY"),
        )

    tools = [build_retriever_tool(vector_store)]

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SECURITY_AGENT_PROMPT
    )

    return agent