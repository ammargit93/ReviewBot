import argparse
from reviewbot.indexing.indexer import index_files
from reviewbot.agents.chat import list_sessions_command, chat_command

def build_parser():
    parser = argparse.ArgumentParser(prog="reviewbot", description="AI code review assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # index command
    index_parser = subparsers.add_parser("index", help="Index files for review")
    index_parser.add_argument("files", nargs="+", help="Files or directories to index")
    index_parser.add_argument("--name",type=str,required=True,help="Conversation name")
    index_parser.set_defaults(func=index_files)
    
    # sessions command
    sessions_parser = subparsers.add_parser("sessions", help="Manage sessions: list / resume / delete")
    sessions_group = sessions_parser.add_mutually_exclusive_group(required=True)
    sessions_group.add_argument("--list", action="store_true", help="List all sessions")
    sessions_group.add_argument("--delete", type=str, help="Delete a session by name")
    sessions_group.add_argument("--resume", type=str, nargs="?", const="", help="Resume a session by name (uses last_session if omitted)")
    sessions_parser.set_defaults(func=list_sessions_command)
    
    # chat command
    chat_parser = subparsers.add_parser("chat",help="Start interactive chat session")
    chat_parser.add_argument("--name",type=str,help="Create a new named session")
    chat_parser.set_defaults(func=chat_command)
    
    return parser