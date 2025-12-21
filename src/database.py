from datetime import datetime
from pathlib import Path, PosixPath
from typing import Any

import redis
from peewee import DateTimeField, Model, Proxy, SqliteDatabase

from src.config import Config, Environment, SQLiteDB
from src.util import get_all_subclasses

_BASE_DIR: PosixPath = Path(__file__).parent

_SQLITE: SqliteDatabase | None = None
_SQLITE_FILE_PATH: PosixPath = _BASE_DIR.parent / "data" / "sqlite.db"
_REDIS: redis.Redis | None = None

_INITIALIZED_DB: bool = False

db_proxy: Proxy = Proxy()


class BaseModel(Model):
    time_created = DateTimeField(default=datetime.now)
    time_updated = DateTimeField(null=True)

    class Meta:
        database = db_proxy

    def save(self, *args, **kwargs) -> bool:
        if self.get_id() is not None:
            self.time_updated = datetime.now()  # type: ignore
        return super().save(*args, **kwargs)

    def update_from_dict(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


def initialize_db(force: bool = False) -> None:
    global _SQLITE, _INITIALIZED_DB
    if _INITIALIZED_DB and not force:
        return
    if _SQLITE is None or force:
        database = (
            ":memory:"
            if Config.sqlite.db == SQLiteDB.MEMORY
            else _SQLITE_FILE_PATH
        )
        _SQLITE = SqliteDatabase(database, pragmas={"foreign_keys": 1})

    _SQLITE.connect()
    db_proxy.initialize(_SQLITE)

    models = get_all_subclasses(BaseModel)
    _SQLITE.create_tables(models)
    _INITIALIZED_DB = True


def redis_pool() -> redis.ConnectionPool:
    global _REDIS
    if not _REDIS:
        _REDIS = redis.ConnectionPool(
            host=Config.redis.host, **Config.redis.options
        )
    return _REDIS


def redis_client() -> Any:
    if not Config.redis.host:
        if Config.environment != Environment.LOCAL:
            raise RuntimeError("Redis host is not configured")
        import fakeredis

        return fakeredis.FakeStrictRedis(server_type="redis")
    return redis.Redis(connection_pool=redis_pool())
