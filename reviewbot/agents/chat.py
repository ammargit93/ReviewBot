import httpx

API_URL = "http://localhost:8000"


async def list_sessions_command(args):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_URL}/session/list")
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
    

async def chat_command(args):
    if not args or not args.name:
        print("Use --name to specify a session")
        return
    session_name = args.name
    print(f"\nSession: {session_name}")
    async with httpx.AsyncClient(timeout=30.0) as client:
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