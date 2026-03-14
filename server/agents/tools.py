from langchain.tools import tool
from tavily import TavilyClient
import re
import os 
from dotenv import load_dotenv
from server.container import ContainerManager

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
        match = re.search(r"[\w./\\-]+\.[a-zA-Z0-9]+", query)
        if match:
            filename = match.group(0)

            docs = vector_store.get(
                where={"path": {"$contains": filename}}
            )

            if docs and docs["documents"]:
                content = "\n\n".join(docs["documents"][:2])

                return (
                    f"### Full file: {filename}\n"
                    f"```\n{content}\n```"
                )

        results = vector_store.similarity_search_with_score(query, k=3)

        formatted = []

        for doc, score in results:
            formatted.append(
                f"### File: {doc.metadata.get('path')}\n"
                f"Score: {score}\n"
                f"```\n{doc.page_content}\n```"
            )

        return "\n\n".join(formatted)

    return search_codebase


@tool
def spawn_container(prompt: str):
    """
    Start a temporary Docker container for sandboxed code execution.
    Returns the container ID.
    """
    manager = ContainerManager()
    container = manager.start_container()
    return {"container_id": container.id}