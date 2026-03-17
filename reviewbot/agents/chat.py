import httpx

API_URL = "http://localhost:8000"


async def list_sessions_command(args):
    if getattr(args, "list", False):
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{API_URL}/session/list")
            except httpx.ConnectError:
                print(f"Error: Could not connect to {API_URL}. Is the server running?")
                return
        if response.status_code != 200:
            print("Error:", response.text)
            return
        data = response.json()
        sessions = data.get("sessions", [])
        if not sessions:
            print("No sessions found.")
            return
        print("\nAvailable Sessions:\n")
        for s in sessions:
            print(f"- {s['session_name']} (messages: {s['message_count']})")
    
    elif getattr(args, "delete", None):
        session_name = args.delete
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(f"{API_URL}/session/{session_name}")
        if response.status_code == 200:
            print(f"Session '{session_name}' deleted successfully.")
        else:
            print(f"Error: {response.text}")
    
    elif getattr(args, "resume", None) is not None:
        session_name = args.resume
        if not session_name:
            from reviewbot.config import LAST_SESSION
            if not LAST_SESSION:
                print("No last session found. Please specify a name to resume.")
                return
            session_name = LAST_SESSION
        
        # update args to pass to chat_command
        args.name = session_name
        await chat_command(args)
    

async def chat_command(args):
    session_name = getattr(args, 'name', None)
    if not session_name:
        from reviewbot.config import LAST_SESSION
        if LAST_SESSION:
            session_name = LAST_SESSION
        else:
            print("Use --name to specify a session, or start a new named session first.")
            return
    
    
    from reviewbot.config import DATA_DIR
    import json
    
    # Save as LAST_SESSION
    try:
        config_file = DATA_DIR / "config.json"
        data = {}
        if config_file.exists():
            data = json.loads(config_file.read_text())
        data["last_session"] = session_name
        config_file.write_text(json.dumps(data, indent=4))
    except Exception:
        pass
    
    print(f"\nSession: {session_name}")
    async with httpx.AsyncClient(timeout=None) as client:
        while True:
            user_input = input("\nEnter : ")
            if user_input == "q":
                break
            response = await client.post(
                f"{API_URL}/chat",
                json={
                    "message": user_input,
                    "thread_id": session_name
                }
            )
            response.raise_for_status()
            results = response.json()
            print(f"\nAI : {results['response']}\n")