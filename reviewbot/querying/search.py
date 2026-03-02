import requests

async def query_command(args):
    query = args.query
    k = 5

    try:
        response = requests.post("http://127.0.0.1:8000/query",json={"query": query,"k": k},timeout=30)
        response.raise_for_status()
        results = response.json()
        
    except Exception as e:
        print(f"Request failed: {e}")
        return

    if not results:
        print("No results found.")
        return

    for r in results:
        print(f"\npath: {r['path']}")
        print(f"content: {r['content']}")
        print(f"score: {r['score']}")