import hashlib
import json
import logging
import os
import shutil
import time
from base64 import b64encode
from enum import StrEnum
from functools import cached_property
from http.client import HTTPSConnection
from pathlib import Path
from typing import Self
from urllib.parse import urlparse

import requests
from peewee import (
    BooleanField,
    CharField,
    CompositeKey,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    TextField,
)
from slugify import slugify

from src.config import Config, Environment, PaprikaClientType
from src.database import BaseModel
from src.util import cache_client

_BASE_DIR = Path(__file__).parent
_IMAGE_DIR = _BASE_DIR / "static" / "images"

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)


class RecipeStatus(StrEnum):
    HIDDEN = "hidden"
    LISTED = "listed"
    SECRET = "secret"


class DoesNotExistError(Exception):
    pass


class ClientError(Exception):
    pass


class Category(BaseModel):
    uid = CharField(primary_key=True)
    order_flag = IntegerField()
    name = CharField()
    parent_uid = CharField(null=True)

    # Admin
    slug = CharField(null=True)
    icon = CharField(null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def hash(self) -> str:
        data = f"{self.uid}{self.order_flag}{self.name}{self.parent_uid}"
        return hashlib.md5(data.encode()).hexdigest()


class Recipe(BaseModel):
    uid = CharField(primary_key=True)
    hash = CharField()
    name = CharField(null=True)
    ingredients = TextField(null=True)
    directions = TextField(null=True)
    description = TextField(null=True)
    notes = TextField(null=True)
    nutritional_info = TextField(null=True)
    servings = CharField(null=True)
    difficulty = CharField(null=True)
    prep_time = CharField(null=True)
    cook_time = CharField(null=True)
    total_time = CharField(null=True)
    source_url = CharField(null=True)
    image_url = CharField(null=True)
    photo = CharField(null=True)
    photo_hash = CharField(null=True)
    photo_large = CharField(null=True)
    scale = CharField(null=True)
    categories = TextField(null=True)
    rating = IntegerField(null=True)
    in_trash = BooleanField(null=True)
    is_pinned = BooleanField(null=True)
    on_favorites = BooleanField(null=True)
    on_grocery_list = BooleanField(null=True)
    created = DateTimeField(null=True)
    photo_url = CharField(null=True)

    # Custom
    slug = CharField(null=True)

    markdown_fields = [
        "ingredients",
        "directions",
        "description",
        "notes",
        "nutritional_info",
    ]

    def is_markdown(self, field) -> str:
        return field in self.markdown_fields

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def trashed(self) -> bool:
        return bool(self.in_trash)

    @property
    def photo_filename(self) -> str:
        parsed_url = urlparse(self.photo_url)
        return os.path.basename(parsed_url.path)

    @property
    def source_domain_name(self) -> str | None:
        if not self.source_url:
            return None
        parsed_url = urlparse(self.source_url)
        return parsed_url.netloc.lstrip("www.")

    @property
    def categories_list(self) -> set[Category]:
        category_uids = CategoryRecipe.select(CategoryRecipe.category).where(
            CategoryRecipe.recipe == self
        )
        return set(Category.select().where(Category.uid.in_(category_uids)))

    @property
    def status(self) -> RecipeStatus:
        categories = {category.name for category in self.categories_list}
        if not Config.paprika.show_uncategorized and not categories:
            return RecipeStatus.HIDDEN
        if categories & set(Config.paprika.hidden_categories):
            return RecipeStatus.HIDDEN
        if categories & set(Config.paprika.secret_categories):
            return RecipeStatus.SECRET
        return RecipeStatus.LISTED


class Photo(BaseModel):
    # From /photos
    uid = CharField(primary_key=True)
    filename = CharField(null=True)
    recipe_uid = CharField(null=True)
    order_flag = IntegerField(null=True)
    name = CharField(null=True)
    hash = CharField(null=True)

    # From /photo
    photo_url = CharField(null=True)


class CategoryRecipe(BaseModel):
    category = ForeignKeyField(Category, on_delete="CASCADE")
    recipe = ForeignKeyField(Recipe, on_delete="CASCADE")

    class Meta:
        primary_key = CompositeKey("category", "recipe")


class PaprikaClient:
    _client: Self | None = None

    _recipes: list[Recipe] | None = None
    _photos: list[Photo] | None = None
    _use_cache: bool = True
    _cache_lock_key: str = "paprika_cache_lock"

    def __init__(self, use_cache: bool = True):
        self._use_cache = use_cache

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    def _request(self, method, endpoint) -> dict:
        raise NotImplementedError

    @classmethod
    def get(cls) -> Self:
        if not cls._client:
            cls._client = (
                PaprikaMockClient()
                if Config.paprika.client == PaprikaClientType.MOCK
                else PaprikaAPIClient()
            )
        return cls._client

    def get_recipes(self) -> list[Recipe]:
        if not self._use_cache or self._recipes is None:
            recipes = self._request("GET", "/api/v1/sync/recipes")
            self.recipes = [Recipe(**recipe) for recipe in recipes]
        return self.recipes

    def get_recipe(self, uid: str) -> Recipe:
        recipe = self._request("GET", f"/api/v1/sync/recipe/{uid}")
        return Recipe(**recipe)

    def get_photos(self) -> list[Photo]:
        if not self._use_cache or self._photos is None:
            photos = self._request("GET", "/api/v1/sync/photos")
            self.photos = [Photo(**photo) for photo in photos]
        return self.photos

    def get_photo(self, uid: str) -> Photo:
        photo = self._request("GET", f"/api/v1/sync/photo/{uid}")
        return Photo(**photo)

    def get_categories(self) -> list[Category]:
        categories = self._request("GET", "/api/v1/sync/categories")
        return [Category(**category) for category in categories]

    def delete_photo(self, path: str) -> None:
        raise NotImplementedError

    def save_photo(self, path: str) -> None:
        raise NotImplementedError


class PaprikaMockClient(PaprikaClient):
    _response_folder = _BASE_DIR / "tests" / "fixtures" / "response_1"

    _temp_dir: Path | None = None

    def __init__(self):
        if Config.environment == Environment.PRODUCTION:
            raise RuntimeError(
                "The mocked client should not be used in production"
            )

    def _request(self, method, endpoint) -> dict:
        response_file = self._response_folder / f"{endpoint.strip('/')}"

        if not response_file.exists():
            raise DoesNotExistError(
                f"Mock response file not found: {response_file}"
            )

        with open(response_file, "r") as file:
            return json.load(file)["result"]

    def delete_photo(self, path: str) -> None:
        dest = _IMAGE_DIR / Path(path).name
        if dest.exists():
            dest.unlink()
            logger.debug(f"Deleted photo: {dest}")
        else:
            logger.debug(f"Photo does not exist: {dest}")

    def save_photo(self, path: str) -> None:
        dest = _IMAGE_DIR / Path(path).name
        if not dest.exists():
            shutil.copyfile(path, dest)
            logger.debug(f"Saved photo to: {dest}")
        else:
            logger.debug(f"Photo already exists: {dest}")


class PaprikaAPIClient(PaprikaClient):
    _conn: HTTPSConnection | None = None
    _base_url: str = "www.paprikaapp.com"
    _request_lock_key: str = "paprika_request_lock"

    @cached_property
    def _headers(self):
        email = Config.paprika.email
        password = Config.paprika.password
        user_and_pass = b64encode(bytes(f"{email}:{password}", "utf-8")).decode(
            "ascii"
        )
        return {"Authorization": f"Basic {user_and_pass}"}

    def __enter__(self):
        self.connection = HTTPSConnection(self._base_url)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()

    def _request(self, method, endpoint) -> dict:
        lock = cache_client()
        while lock.get(key=self._request_lock_key):
            time.sleep(Config.paprika.api_delay / 2)

        self.connection.request(method, endpoint, headers=self._headers)
        response = self.connection.getresponse().read()
        result = json.loads(response)

        if (
            "error" in result
            and "not found" in result["error"]["message"].lower()
        ):
            raise DoesNotExistError("Record not found")
        elif "result" in result:
            result = result["result"]
        else:
            raise ClientError("Error retrieving data from Paprika")

        lock.setex(
            key=self._request_lock_key, ttl=Config.paprika.api_delay, value=True
        )

        return result

    def delete_photo(self, path: str) -> None:
        parsed_url = urlparse(path)
        dest = _IMAGE_DIR / Path(parsed_url.path).name
        if dest.exists():
            dest.unlink()
            logger.debug(f"Deleted photo: {dest}")
        else:
            logger.debug(f"Photo does not exist: {dest}")

    def save_photo(self, path: str) -> None:
        parsed_url = urlparse(path)
        dest = _IMAGE_DIR / Path(parsed_url.path).name
        if not dest.exists():
            with requests.get(path, stream=True) as response:
                response.raise_for_status()
                response.raw.decode_content = True
                with open(dest, "wb") as file:
                    shutil.copyfileobj(response.raw, file)
                logger.debug(f"Saved photo to: {dest}")
        else:
            logger.debug(f"Photo already exists: {dest}")
