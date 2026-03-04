from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from langchain_chroma import Chroma
from langchain_core.documents import Document
from tortoise.contrib.fastapi import register_tortoise

from pathlib import Path
import hashlib
from uuid import uuid4
import time

from reviewbot.config import COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, DB_PATH
from .agents.llm import create_rag_agent, generate_ai_response
from .models import Session, File
from .utils import document_splitter


# ------------------ LIFESPAN ------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading embedding model and Chroma...")

    vector_store = Chroma(
        collection_name=COLLECTION,
        persist_directory=str(CHROMA_PATH),
        embedding_function=EMBEDDING_MODEL,
    )

    agent = create_rag_agent(vector_store)

    app.state.vector_store = vector_store
    app.state.agent = agent

    print("ReviewBot server ready")

    yield

    print("Shutting down ReviewBot server")


# ------------------ APP INIT ------------------

app = FastAPI(lifespan=lifespan)

# 🔥 REGISTER TORTOISE AFTER APP CREATION
register_tortoise(
    app,
    db_url=f"sqlite://{DB_PATH}",
    modules={"models": ["server.models"]},  # ⚠️ FIX THIS IF NEEDED
    generate_schemas=True,
    add_exception_handlers=True,
)


# ------------------ CHAT ------------------

@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()

    message = body.get("message")
    thread_id = body.get("thread_id")

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")

    response = await generate_ai_response(
        agent=request.app.state.agent,
        user_input=message,
        thread_id=thread_id,
    )

    return {"response": response}


# ------------------ INDEX ------------------
from fastapi import HTTPException
from .services.indexer import run_indexing


@app.post("/index")
async def index_files(request: Request):
    try:
        body = await request.json()
        paths = body.get("paths", [])
        session_name = body.get("session_name")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not session_name:
        raise HTTPException(
            status_code=400,
            detail="session_name is required"
        )

    if not paths:
        raise HTTPException(
            status_code=400,
            detail="paths list is required"
        )

    vector_store = request.app.state.vector_store

    result = await run_indexing(
        paths=paths,
        session_name=session_name,
        vector_store=vector_store
    )

    return result