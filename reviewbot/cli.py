import argparse
from reviewbot.indexing.indexer import index_files
from reviewbot.querying.search import query_command


def build_parser():
    parser = argparse.ArgumentParser(prog="reviewbot", description="AI code review assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # index command
    index_parser = subparsers.add_parser("index", help="Index files for review")
    index_parser.add_argument("files", nargs="+", help="Files or directories to index")
    index_parser.set_defaults(func=index_files)
    
    # query command
    query_parser = subparsers.add_parser("query", help="Query indexed code")
    query_parser.add_argument("query", help="Natural language query")
    query_parser.set_defaults(func=query_command)

    return parser