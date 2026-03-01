from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings

CWD = Path.cwd()
COLLECTION = CWD.name
CHROMA_PATH = CWD / ".reviewbot" / "embeddings"
DB_DIR = Path(".reviewbot") / "database"
DB_PATH = DB_DIR / "reviewbot.db"

EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")