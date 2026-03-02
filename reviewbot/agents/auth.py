from reviewbot.models import Conversation
from typing import Optional, Any

CONVERSATION_NAME : Conversation = None

async def create_conversation_command(args:Optional[Any] = None):
    if not args:
        convo_name = input("Conversation name: ").strip()
    if not args:
        print("Conversation name cannot be empty")
        return

    convo, created = await Conversation.get_or_create(conversation_name=convo_name)
    if created:
        print(f"\nCreated new conversation: {convo.conversation_name}")
    else:
        print(f"\nLoaded existing conversation: {convo.conversation_name}")
    print(f"Conversation ID: {convo.id}")

    return convo