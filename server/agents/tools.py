from langchain.tools import tool
from tavily import TavilyClient
import re
import os
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

MAX_TOOL_OUTPUT = 2500  # hard safety limit


@tool(return_direct=True)
def search_web(query: str):
    """Search the web for information."""
    results = str(client.search(query))

    if len(results) > 2000:
        results = results[:2000] + "\n...[TRUNCATED]"

    return results


def build_retriever_tool(vector_store, session_name):

    @tool
    def search_codebase(query: str) -> str:
        """
        Search the indexed codebase for relevant code snippets or files.
        Works across any programming language.
        """

        output = ""

        # ---------- FILE LOOKUP ----------
        match = re.search(r"[\w./\\-]+\.[a-zA-Z0-9]+", query)

        if match:
            filename = match.group(0)

            docs = vector_store.get(
                where={"path": {"$contains": filename}}
            )

            if docs and docs["documents"]:
                content = docs["documents"][0]

                if len(content) > 1500:
                    content = content[:1500] + "\n...[TRUNCATED]"

                output = (
                    f"### File: {filename}\n"
                    f"```\n{content}\n```"
                )

        # ---------- VECTOR SEARCH ----------
        if not output:
            results = vector_store.max_marginal_relevance_search(
                query,
                k=4,
                fetch_k=12,
                filter={"session": session_name}
            )

            formatted = []

            for doc in results:

                content = doc.page_content

                if len(content) > 600:
                    content = content[:600] + "\n...[TRUNCATED]"

                formatted.append(
                    f"### File: {doc.metadata.get('path')}\n"
                    f"```\n{content}\n```"
                )
            # results = vector_store.similarity_search_with_score(
            #     query,
            #     k=3,  # reduced from 3
            #     filter={"session": session_name}
            # )

            # formatted = []

            # for doc, score in results:

            #     content = doc.page_content

            #     if len(content) > 600:
            #         content = content[:600] + "\n...[TRUNCATED]"

            #     formatted.append(
            #         f"### File: {doc.metadata.get('path')}\n"
            #         f"Score: {round(score,3)}\n"
            #         f"```\n{content}\n```"
            #     )

            output = "\n\n".join(formatted)

        # ---------- FINAL SAFETY TRUNCATION ----------
        if len(output) > MAX_TOOL_OUTPUT:
            output = output[:MAX_TOOL_OUTPUT] + "\n...[FINAL_TRUNCATION_TO_AVOID_TOKEN_LIMIT]"

        return output

    return search_codebase