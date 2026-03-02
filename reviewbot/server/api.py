from fastapi import FastAPI
from contextlib import asynccontextmanager
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel
from pathlib import Path

from langchain_chroma import Chroma
from reviewbot.config import COLLECTION, CHROMA_PATH, EMBEDDING_MODEL


vector_store = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_store

    print("Loading embedding model and Chroma...")

    app.state.vector_store = Chroma(
        collection_name=COLLECTION,
        persist_directory=str(CHROMA_PATH),
        embedding_function=EMBEDDING_MODEL
    )

    print("ReviewBot server ready")

    yield

    print("Shutting down ReviewBot server")


app = FastAPI(lifespan=lifespan)


class QueryRequest(BaseModel):
    query: str
    k: int = 5


@app.post("/query")
async def query(request: QueryRequest):

    results = app.state.vector_store.similarity_search_with_score(
        request.query,
        k=request.k
    )

    return [
        {
            "path": doc.metadata["path"],
            "content": doc.page_content,
            "score": score
        }
        for doc, score in results
    ]