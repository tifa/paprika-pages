import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import PaprikaClientType, SQLiteDB
from src.database import initialize_db


@pytest.fixture(autouse=True)
def db():
    with (
        tempfile.TemporaryDirectory() as temp_dir,
        patch("src.database.Config.sqlite.db", return_value=SQLiteDB.MEMORY),
        patch(
            "src.paprika.Config.paprika.client",
            return_value=PaprikaClientType.MOCK,
        ),
        patch("src.paprika._IMAGE_DIR", Path(temp_dir)),
    ):
        initialize_db(force=True)
        yield
