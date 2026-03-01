from tortoise.models import Model
from tortoise import fields

class File(Model):
    id = fields.IntField(primary_key=True)
    file_path = fields.CharField(max_length=500)
    file_hash = fields.CharField(max_length=64)
    file_embed_id = fields.CharField(max_length=36)