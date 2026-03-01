import os
from tortoise import Tortoise
from .config import DB_DIR, DB_PATH
from .cli import build_parser

async def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    from .models import File  # import models before init
    await Tortoise.init(db_url=f"sqlite://{DB_PATH}", modules={"models": ["reviewbot.models"]})
    await Tortoise.generate_schemas()

async def main():
    await init_db()
    parser = build_parser()
    args = parser.parse_args()
    await args.func(args)
    await Tortoise.close_connections()