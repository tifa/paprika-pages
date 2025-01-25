from enum import StrEnum
from pathlib import Path

from dynaconf import Dynaconf, Validator

_BASE_DIR = Path(__file__).parent

STATIC_DIR = _BASE_DIR / "static"
MAINTENANCE_FILE = "/tmp/maintenance_mode"


class Environment(StrEnum):
    LOCAL = "local"
    PRODUCTION = "production"


class SQLiteDB(StrEnum):
    FILE = "file"
    MEMORY = "memory"


class PaprikaClientType(StrEnum):
    MOCK = "mock"
    API = "api"


EnvConfig = Dynaconf(
    load_dotenv=True,
    settings_files=[_BASE_DIR.parent / ".env"],
    envvar_prefix="PROJECT",
    validators=[
        Validator("hostname", must_exist=True, is_type_of=str),
        Validator("name", must_exist=True, is_type_of=str),
    ],
)

Config = Dynaconf(
    settings_files=[_BASE_DIR.parent / "config.toml"],
    validators=[
        Validator("title", must_exist=True, is_type_of=str),
        Validator("sqlite.db", must_exist=True, is_in=SQLiteDB),
        Validator("redis.host", must_exist=True, is_type_of=str),
        Validator("redis.options", is_type_of=dict, default={}),
        Validator("paprika.client", must_exist=True, is_in=PaprikaClientType),
        Validator("paprika.api_delay", is_type_of=int, default=1),
        Validator("paprika.email", must_exist=True, is_type_of=str),
        Validator("paprika.password", must_exist=True, is_type_of=str),
        Validator("paprika.secret_categories", is_type_of=list),
        Validator("paprika.hidden_categories", is_type_of=list),
        Validator("paprika.show_uncategorized", is_type_of=bool, default=True),
    ],
)

Config.update(
    {
        "environment": EnvConfig.environment,
        "hostname": EnvConfig.hostname,
        "project_name": EnvConfig.name,
    }
)
