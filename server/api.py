from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from langchain_chroma import Chroma
from tortoise.contrib.fastapi import register_tortoise


from reviewbot.config import COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, DB_PATH
from .agents.llm import create_rag_agent, generate_ai_response

from fastapi import HTTPException
from .services.indexer import run_indexing
from .services.sessions import router as session_router
from .models import Session, Message



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



app = FastAPI(lifespan=lifespan)
app.include_router(session_router)

register_tortoise(
    app,
    db_url=f"sqlite://{DB_PATH}",
    modules={"models": ["server.models"]}, 
    generate_schemas=True,
    add_exception_handlers=True,
)

@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()

    message = body.get("message")
    thread_id = body.get("thread_id")

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")

    session, _ = await Session.get_or_create(session_name=thread_id)

    # store user message
    await Message.create(
        session=session,
        message_content=message,
        message_type="HumanMessage"
    )

    response = await generate_ai_response(
        agent=request.app.state.agent,
        user_input=message,
        thread_id=thread_id,
    )

    # store AI message
    await Message.create(
        session=session,
        message_content=response,
        message_type="AIMessage"
    )

    session.message_count += 2
    await session.save()

    return {
        "response": response
    }


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