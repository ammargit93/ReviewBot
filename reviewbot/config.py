from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings

# Base directory = project being indexed
BASE_DIR = Path.cwd().resolve()

# ReviewBot data folder inside project
DATA_DIR = BASE_DIR / ".reviewbot"

# Vector store directory
CHROMA_PATH = DATA_DIR / "embeddings"

# SQLite database
DB_DIR = DATA_DIR / "database"
DB_PATH = DB_DIR / "reviewbot.db"

# Collection name = project folder name
COLLECTION = BASE_DIR.name

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PATH.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

# Embedding model
EMBEDDING_MODEL = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Ignore directories during indexing
IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".reviewbot",
    "node_modules",
}