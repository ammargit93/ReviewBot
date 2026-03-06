from fastapi import APIRouter, HTTPException, Request
from server.services.indexer import run_indexing

router = APIRouter()


@router.post("/index")
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