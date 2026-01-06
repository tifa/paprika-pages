from datetime import datetime
from pathlib import Path, PosixPath

from peewee import DateTimeField, Model, Proxy, SqliteDatabase

from src.config import Config, SQLiteDB
from src.util import get_all_subclasses

_BASE_DIR: PosixPath = Path(__file__).parent

_SQLITE: SqliteDatabase | None = None
_SQLITE_FILE_PATH: PosixPath = _BASE_DIR.parent / "data" / "sqlite.db"

_INITIALIZED_DB: bool = False


class LazyProxy(Proxy):
    def __getattr__(self, attr):
        if self.obj is None:
            initialize_db(force=True)
        return super().__getattr__(attr)


db_proxy: Proxy = LazyProxy()


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
