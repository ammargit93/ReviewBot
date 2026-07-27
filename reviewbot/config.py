import os
os.environ["HF_TOKEN"] = ""

from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
import json

# Base directory = project being indexed
BASE_DIR = Path.cwd().resolve()

# ReviewBot data folder inside project
DATA_DIR = BASE_DIR / ".reviewbot"

# Vector store directory
CHROMA_PATH = DATA_DIR / "embeddings"

# snapshots
SNAPSHOT_PATH = DATA_DIR / "snapshots"

# SQLite database
DB_DIR = DATA_DIR / "database"
DB_PATH = DB_DIR / "reviewbot.db"
SNAPSHOT_PATH = DATA_DIR / "snapshots"

# Collection name = project folder name
COLLECTION = BASE_DIR.name

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PATH.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_PATH.mkdir(parents=True, exist_ok=True)

# Embedding model
EMBEDDING_MODEL = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"token": False}
)

# Ignore directories during indexing
IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".reviewbot",
    "node_modules",
    "assets",
    ".python-version",
    "uv.lock"
}

LAST_SESSION = None

def load_config():
    global LAST_SESSION
    config_file = DATA_DIR / "config.json"
    if not config_file.exists():
        config_file.write_text(json.dumps({"last_session": None}, indent=4))
    
    try:
        config_data = json.loads(config_file.read_text())
        LAST_SESSION = config_data.get("last_session")
    except Exception:
        pass

load_config()