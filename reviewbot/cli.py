import argparse
from reviewbot.indexing.indexer import index_files
from reviewbot.querying.search import query_command
from reviewbot.agents.auth import create_conversation_command

def build_parser():
    parser = argparse.ArgumentParser(prog="reviewbot", description="AI code review assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # index command
    index_parser = subparsers.add_parser("index", help="Index files for review")
    index_parser.add_argument("files", nargs="+", help="Files or directories to index")
    index_parser.add_argument("--name",type=str,required=True,help="Conversation name")
    index_parser.set_defaults(func=index_files)
    
    # query command
    query_parser = subparsers.add_parser("query", help="Query indexed code")
    query_parser.add_argument("query", help="Natural language query")
    query_parser.set_defaults(func=query_command)

    # create_conversation_command
    login_parser = subparsers.add_parser("login",help="Create or load a Conversation in ReviewBot")
    login_parser.add_argument("--name",type=str,help="Conversation name")
    login_parser.set_defaults(func=create_conversation_command)    
    
    return parser