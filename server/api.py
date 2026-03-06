from contextlib import asynccontextmanager
from langchain_chroma import Chroma
from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI

from reviewbot.config import COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, DB_PATH
from .agents.llm import create_rag_agent

from .routes.session_route import router as session_router
from .routes.index_route import router as index_router
from .routes.chat_route import router as chat_router
from .watcher import start_watcher

observer = None

def reindex_file(path):
    # call your index logic here
    pass

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
    observer = start_watcher(
        path=".", 
        index_func=reindex_file
    )
    print("loaded observer")
    yield
    
    observer.stop()
    observer.join()
    
    print("Shutting down observer thread")
    print("Shutting down ReviewBot server")


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
