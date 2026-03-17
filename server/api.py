from contextlib import asynccontextmanager
from fastapi import FastAPI
from langchain_chroma import Chroma
from tortoise.contrib.fastapi import register_tortoise

from reviewbot.config import COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, DB_PATH

from .agents.llm import create_rag_agent
from .routes.session_route import router as session_router
from .routes.index_route import router as index_router
from .routes.chat_route import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading Chroma vector store...")

    vector_store = Chroma(
        collection_name=COLLECTION,
        persist_directory=str(CHROMA_PATH),
        embedding_function=EMBEDDING_MODEL,
    )

    # agent = create_rag_agent(vector_store, session_name=None)
    app.state.vector_store = vector_store
    app.state.agent = None

    print("ReviewBot server ready")
    yield

    print("ReviewBot server shutdown")


app = FastAPI(lifespan=lifespan)

app.include_router(session_router)
app.include_router(index_router)
app.include_router(chat_router)

register_tortoise(
    app,
    db_url=f"sqlite://{DB_PATH}",
    modules={"models": ["server.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)