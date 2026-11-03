from functools import lru_cache
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from gestion_documental.config import get_settings


@lru_cache
def get_client() -> MongoClient[dict[str, Any]]:
    return MongoClient(get_settings().mongo_uri, serverSelectionTimeoutMS=5000)


def get_db() -> Database[dict[str, Any]]:
    return get_client()[get_settings().mongo_db]


def ping(db: Database[dict[str, Any]]) -> bool:
    try:
        db.command("ping")
    except PyMongoError:
        return False
    return True
