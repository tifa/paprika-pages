from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

import pytest

from src.paprika import Recipe


class TestRecipe:
    @pytest.mark.parametrize(
        "device_timezone",
        [
            ("America/New_York"),
            ("Australia/Sydney"),
        ],
    )
    def test_from_api(self, device_timezone):
        original_created = "2024-06-15 12:00:00"
        data = {
            "uid": "test-uid",
            "title": "Test Recipe",
            "created": original_created,
        }

        with mock.patch("src.paprika.Config.paprika.timezone", device_timezone):
            recipe = Recipe.from_api(data)

        date_format = "%Y-%m-%d %H:%M:%S"
        timezone = ZoneInfo(device_timezone)
        naive_date = datetime.strptime(original_created, date_format)
        local_date = naive_date.replace(tzinfo=timezone)
        expected_utc = local_date.astimezone(ZoneInfo("UTC"))
        expected_utc_str = expected_utc.strftime(date_format)
        assert recipe.created == expected_utc_str
