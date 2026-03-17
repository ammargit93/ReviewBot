from fastapi import APIRouter, Request, HTTPException
from server.models import Session, Message
from server.agents.llm import generate_ai_response, create_rag_agent
from langchain.messages import HumanMessage

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()

    message = body.get("message")
    thread_id = body.get("thread_id")
    print(message)
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")

    # get or create session
    session, _ = await Session.get_or_create(session_name=thread_id)

    if not request.app.state.agent:
        request.app.state.agent = create_rag_agent(request.app.state.vector_store, thread_id)

    # store user message
    await Message.create(
        session=session,
        message_content=message,
        message_type="HumanMessage"
    )
    print(message)

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

    return {"response": response}