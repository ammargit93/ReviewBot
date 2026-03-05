from fastapi import APIRouter, HTTPException, Request
from server.models import Session

router = APIRouter()



@router.get("/session/list")
async def list_sessions():
    sessions = await Session.all()
    return {
        "sessions": [
            {
                "session_name": s.session_name,
                "message_count": s.message_count
            }
            for s in sessions
        ]
    }