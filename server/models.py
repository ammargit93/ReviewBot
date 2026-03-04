from tortoise.models import Model
from tortoise import fields


class Session(Model):
    id = fields.IntField(primary_key=True)
    session_name = fields.CharField(max_length=500)
    files: fields.ReverseRelation["File"]
    messages: fields.ReverseRelation["Message"]
    message_count = fields.IntField(default=0)
    session_created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return f"Session(id={self.id}, name={self.session_name})"


class File(Model):
    id = fields.IntField(primary_key=True)
    session = fields.ForeignKeyField("models.Session",related_name="files",on_delete=fields.CASCADE)
    file_path = fields.CharField(max_length=500)
    file_hash = fields.CharField(max_length=64)
    file_embed_id = fields.CharField(max_length=36, null=True)
    file_indexed_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return f"File(id={self.id}, path={self.file_path})"


class Message(Model):
    id = fields.IntField(primary_key=True)
    session = fields.ForeignKeyField("models.Session",related_name="messages",on_delete=fields.CASCADE)
    message_content = fields.TextField()
    message_type = fields.CharField(max_length=20)  
    message_created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return f"Message(id={self.id}, type={self.message_type})"