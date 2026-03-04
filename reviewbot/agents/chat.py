from reviewbot.models import Session, Message
from typing import Optional, Any
import requests

async def create_session_command(args:Optional[Any] = None):
    if not args:
        session_name = input("Session name: ").strip()
    if not session_name:
        print("Session name cannot be empty")
        return

    session, created = await Session.get_or_create(session_name=session_name)
    if created:
        print(f"\nCreated new session: {session.session_name}")
    else:
        print(f"\nLoaded existing session: {session.session_name}")
    print(f"Session ID: {session.id}")

    return session



async def list_sessions_command(args):
    sessions = await Session.all()
    if not sessions:
        print("No sessions found.")
        return
    print("\nAvailable Sessions:\n")
    for s in sessions:
        print(f"- {s.session_name} (messages: {s.message_count})")
        
        
async def chat_command(args):
    if args:
        session_name = args.name
        session, created = await Session.get_or_create(session_name=session_name)
        if created:
            print(f"\nCreated new session: {session.session_name}")
        else:

            print(f"\nLoaded existing session: {session.session_name}")
            while True:
                user_input = input("\nEnter : ")
                
                response = requests.post("http://127.0.0.1:8000/chat",json={"message": user_input,"thread_id": session_name},timeout=30)
                response.raise_for_status()
                results = response.json() 
                
                await Message.create(session=session, message_content=results["response"], message_type="HumanMessage")

                if user_input=="q":
                    break
                
                
                await Message.create(session=session, message_content=results["response"], message_type="AIMessage")
                session.message_count += 2
                await session.save()
                
                print(f"\nAI : {results["response"]}\n")
    else:
        sessions = await Session.all()
        print("\nAvailable Sessions:\n")
        for s in sessions:
            print(f"- {s.session_name} (messages: {s.message_count})")
        print("Use --name to select a session.")
        
async def load_messages(session_name):
    session = await Session.get(session_name=session_name)
    return await Message.filter(session=session)