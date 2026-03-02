import hashlib
from uuid import uuid4
from langchain_core.documents import Document
from langchain_chroma import Chroma
import requests
import time

from reviewbot.models import File, Conversation
from reviewbot.indexing.chunking import document_splitter
from reviewbot.config import COLLECTION, CHROMA_PATH, EMBEDDING_MODEL
from reviewbot.utils import resolve_files
from reviewbot.agents.auth import create_conversation_command

IGNORE_DIRS = {".git", ".venv", "__pycache__", ".reviewbot", "node_modules"}

async def index_files(args):
    start = time.perf_counter()
    all_files = resolve_files(args)
    
    if not all_files:
        print("No files to index")
        return
    
    convo_name = args.name
    if not convo_name:
        convo_name = input("Conversation name: ").strip()

    convo, _ = await Conversation.get_or_create(
        conversation_name=convo_name
    )
    
    vector_store = Chroma(
        collection_name=COLLECTION,
        persist_directory=str(CHROMA_PATH),
        embedding_function=EMBEDDING_MODEL
    )

    documents, uuids = [], []
    
    for filepath in all_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Failed reading {filepath}: {e}")
            continue

        filehash = hashlib.sha1(content.encode("utf-8")).hexdigest()
        file_id = str(uuid4())

        documents.append(Document(page_content=content, metadata={"path": str(filepath)}, id=file_id))
        uuids.append(file_id)

        await File.create(convo=convo, file_path=str(filepath), file_hash=filehash, file_embed_id=file_id)
        print(f"Indexed: {filepath}")

    if documents:
        docs, uuids = document_splitter(documents=documents)
        vector_store.add_documents(documents=docs, ids=uuids)
        end = time.perf_counter()
        print(f"\nIndexed {len(documents)} files successfully.")
        print(f"\nIndexing completed in {end - start:.4f} seconds")


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