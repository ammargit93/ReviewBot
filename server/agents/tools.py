from langchain.tools import tool
from tavily import TavilyClient
import re
import os 
from dotenv import load_dotenv

load_dotenv()
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def search_web(query: str):
    """Search the web for information."""
    return client.search(query)


def build_retriever_tool(vector_store):

    @tool
    def search_codebase(query: str) -> str:
        """
        Search the indexed codebase for relevant code snippets or files.
        Works across any programming language.
        """

        # detect any filename with extension
        match = re.search(r"[\w./\\-]+\.[a-zA-Z0-9]+", query)
        
        if match:
            filename = match.group(0)

            docs = vector_store.get(
                where={"path": {"$contains": filename}}
            )

            if docs and docs["documents"]:
                content = "\n\n".join(docs["documents"])

                return (
                    f"### Full file: {filename}\n"
                    f"```\n{content}\n```"
                )

        # semantic search fallback
        results = vector_store.similarity_search_with_score(query, k=5)

        formatted = []

        for doc, score in results:
            formatted.append(
                f"### File: {doc.metadata.get('path')}\n"
                f"Score: {score}\n"
                f"```\n{doc.page_content}\n```"
            )

        return "\n\n".join(formatted)

    return search_codebase

