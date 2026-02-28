import os
from tortoise import Tortoise
import argparse
from tortoise.models import Model
from tortoise import fields
import hashlib
from pathlib import Path
from uuid import uuid4
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


CWD = Path.cwd()
COLLECTION = Path(CWD).name
CHROMA_PATH = Path(CWD) / ".reviewbot" / "embeddings"
DB_DIR = Path(".reviewbot") / "database" 
DB_PATH = DB_DIR / "reviewbot.db"
EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


class File(Model):
    id = fields.IntField(primary_key=True)
    file_path = fields.CharField(max_length=255)
    file_hash = fields.CharField(max_length=255)
    file_content = fields.TextField()
    file_embed_id = fields.CharField(max_length=255)



async def index_files(args):
    all_files = []

    for input_path in args.files:
        path = Path(input_path).resolve()

        if not path.exists():
            print(f"File not found: {path}")
            continue

        if path.is_file():
            all_files.append(path)
        else:
            all_files.extend(p for p in path.rglob("*") if p.is_file())

    if not all_files:
        print("No files to index")
        return

    vector_store = Chroma(
        collection_name=COLLECTION,
        persist_directory=CHROMA_PATH,
        embedding_function=EMBEDDING_MODEL
    )

    documents = []
    uuids = []
    
    for idx, filepath in enumerate(all_files):

        try:
            content = filepath.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception as e:
            print(f"Failed reading {filepath}: {e}")
            continue

        filehash = hashlib.sha1(content.encode("utf-8")).hexdigest()

        file_id = str(uuid4())

        documents.append(
            Document(
                page_content=content,
                metadata={"path": str(filepath)},
                id=file_id
            )
        )

        uuids.append(file_id)

        await File.create(
            file_path=str(filepath),
            file_hash=filehash,
            file_content=content,
            file_embed_id=file_id,
        )

        print(f"Indexed: {filepath}")

    if documents:
        vector_store.add_documents(
            documents=documents,
            ids=uuids
        )
        print(f"\nIndexed {len(documents)} files successfully.")
    

async def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(CHROMA_PATH, exist_ok=True)
    await Tortoise.init(
        db_url=f"sqlite://{DB_PATH}",
        modules={"models": ["reviewbot.main"]}
    )
    await Tortoise.generate_schemas()
    

def build_parser():
    parser = argparse.ArgumentParser(
        prog="reviewbot", description="AI code review assistant"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # index command
    index_parser = subparsers.add_parser("index", help="Index files for review")
    
    index_parser.add_argument(
        "files", nargs="+", help="Files to index"  # one or more files
    )
    
    index_parser.set_defaults(func=index_files)
    return parser


async def main():
    await init_db()

    parser = build_parser()
    args = parser.parse_args()

    await args.func(args)   

    await Tortoise.close_connections()
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())