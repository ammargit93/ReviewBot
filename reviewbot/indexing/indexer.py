import requests
import time
from reviewbot.utils import resolve_files
from reviewbot.config import DATA_DIR
import json

IGNORE_DIRS = {".git", ".venv", "__pycache__", ".reviewbot", "node_modules"}

async def index_files(args):
    start = time.perf_counter()

    all_files = resolve_files(args)

    if not all_files:
        print("No files to index")
        return

    session_name = args.name
    incremental = args.incremental
    if not session_name:
        session_name = input("Session name: ").strip()

    file_paths = [str(p) for p in all_files]
    
        
    try:
        response = requests.post(
            "http://127.0.0.1:8000/index",
            json={
                "paths": file_paths,
                "session_name": session_name,
                "incremental":incremental,
            },
            timeout=600
        )

        response.raise_for_status()
        result = response.json()

    except Exception as e:
        print(f"Indexing request failed: {e}")
        return

    end = time.perf_counter()
    
    try:
        config_file = DATA_DIR / "config.json"
        data = {}
        if config_file.exists():
            data = json.loads(config_file.read_text())
        data["last_session"] = session_name
        config_file.write_text(json.dumps(data, indent=4))
    except Exception:
        print(f"Could not save last session")

    print("\nIndexing completed successfully.")
    print(f"Files indexed: {result.get('indexed_files', 0)}")
    print(f"Server time taken: {result.get('time_taken_seconds')} seconds")
    print(f"Total CLI time: {end - start:.4f} seconds")