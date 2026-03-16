from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

from .tools import build_retriever_tool

load_dotenv()

SECURITY_AGENT_PROMPT = """
You are a specialized Security Review Agent focusing exclusively on identifying
security vulnerabilities in code.

You MUST retrieve code using the `search_codebase` tool before performing analysis.
Never invent vulnerabilities or code.

Focus specifically on:
- authentication or authorization vulnerabilities
- command injection or shell injection risks
- unsafe file handling
- path traversal vulnerabilities
- hardcoded secrets or credentials
- potential denial-of-service conditions

If vulnerabilities exist, return a structured report containing:
- Summary of findings
- List of detected vulnerabilities
- Code locations
- Suggested fixes

If no vulnerabilities are detected after analyzing the retrieved code,
return exactly:

No security issues found.
"""

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