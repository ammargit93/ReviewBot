from fastapi import APIRouter, HTTPException
from server.models import Session
router = APIRouter()

@router.get("/session/list")
async def list_sessions():
    sessions = await Session.all().values("session_name", "message_count")
    return {
        "sessions": [
            {
                "session_name": s["session_name"],
                "message_count": s["message_count"]
            }
            for s in sessions
        ]
    }

@router.delete("/session/{session_name}")
async def delete_session(session_name: str):
    session = await Session.get_or_none(session_name=session_name)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await session.delete()
    return {"status": "success"}