from datetime import datetime
from unittest.mock import patch

import pytest

from src.paprika import _BASE_DIR as PAPRIKA_BASE_DIR
from src.paprika import Category, Photo, Recipe
from src.sync import sync_categories, sync_photos, sync_recipes


@pytest.fixture
def recipes():
    response_0 = {}
    response_1 = {
        "recipe-1-uid": Recipe(
            uid="recipe-1-uid",
            name="Recipe 1 Name",
            ingredients="Recipe 1 ingredients",
            directions="Recipe 1 description",
            description="Recipe 1 description",
            notes="Recipe 1 notes",
            nutritional_info="Recipe 1 calories",
            servings="Recipe 1 servings",
            difficulty="Recipe 1 difficulty",
            prep_time="Recipe 1 prep time",
            cook_time="Recipe 1 cook time",
            total_time="Recipe 1 total time",
            source="Recipe 1 source",
            source_url="https://example.net/recipe-1-source-url",
            image_url=None,
            photo="recipe-1-photo.png",
            photo_hash="recipe-1-photo-hash",
            photo_large="recipe-1-photo-large.png",
            scale="Recipe 1 scale",
            hash="recipe-1-hash",
            categories="[]",
            rating=0,
            in_trash=False,
            is_pinned=False,
            on_favorites=False,
            on_grocery_list=False,
            created=datetime(2000, 1, 1, 5, 0, 0),
            photo_url="src/tests/fixtures/photos/photo-1-cover.png",
            slug="recipe-1-name",
        ),
        "recipe-2-uid": Recipe(
            uid="recipe-2-uid",
            name="Recipe 2 Name",
            ingredients="Recipe 2 ingredients",
            directions="Recipe 2 description",
            description="Recipe 2 description",
            notes="Recipe 2 notes",
            nutritional_info="Recipe 2 calories",
            servings="Recipe 2 servings",
            difficulty="Recipe 2 difficulty",
            prep_time="Recipe 2 prep time",
            cook_time="Recipe 2 cook time",
            total_time="Recipe 2 total time",
            source="Recipe 2 source",
            source_url="https://example.net/recipe-2-source-url",
            image_url=None,
            photo="recipe-2-photo.png",
            photo_hash="recipe-2-photo-hash",
            photo_large="recipe-2-photo-large.png",
            scale="Recipe 2 scale",
            hash="recipe-2-hash",
            categories="[]",
            rating=0,
            in_trash=False,
            is_pinned=False,
            on_favorites=False,
            on_grocery_list=False,
            created=datetime(2000, 1, 1, 5, 0, 0),
            photo_url="src/tests/fixtures/photos/photo-2-cover.png",
            slug="recipe-2-name",
        ),
        "recipe-3-uid": Recipe(
            uid="recipe-3-uid",
            name="Recipe 3 Name",
            ingredients="Recipe 3 ingredients",
            directions="Recipe 3 description",
            description="Recipe 3 description",
            notes="Recipe 3 notes",
            nutritional_info="Recipe 3 calories",
            servings="Recipe 3 servings",
            difficulty="Recipe 3 difficulty",
            prep_time="Recipe 3 prep time",
            cook_time="Recipe 3 cook time",
            total_time="Recipe 3 total time",
            source="Recipe 3 source",
            source_url="https://example.net/recipe-3-source-url",
            image_url=None,
            photo="recipe-3-photo.png",
            photo_hash="recipe-3-photo-hash",
            photo_large="recipe-3-photo-large.png",
            scale="Recipe 3 scale",
            hash="recipe-3-hash",
            categories="[]",
            rating=0,
            in_trash=False,
            is_pinned=False,
            on_favorites=False,
            on_grocery_list=False,
            created=datetime(2000, 1, 1, 5, 0, 0),
            photo_url="src/tests/fixtures/photos/photo-3-cover.png",
            slug="recipe-3-name",
        ),
    }
    response_2 = {
        "recipe-1-uid": Recipe(
            uid="recipe-1-uid",
            name="Recipe 1 Name",
            ingredients="Recipe 1 ingredients",
            directions="Recipe 1 description",
            description="Recipe 1 description",
            notes="Recipe 1 notes",
            nutritional_info="Recipe 1 calories",
            servings="Recipe 1 servings",
            difficulty="Recipe 1 difficulty",
            prep_time="Recipe 1 prep time",
            cook_time="Recipe 1 cook time",
            total_time="Recipe 1 total time",
            source="Recipe 1 source",
            source_url="https://example.net/recipe-1-source-url",
            image_url=None,
            photo="recipe-1-photo.png",
            photo_hash="recipe-1-photo-hash",
            photo_large="recipe-1-photo-large.png",
            scale="Recipe 1 scale",
            hash="recipe-1-hash",
            categories="[]",
            rating=0,
            in_trash=False,
            is_pinned=False,
            on_favorites=False,
            on_grocery_list=False,
            created=datetime(2000, 1, 1, 5, 0, 0),
            photo_url="src/tests/fixtures/photos/photo-1-cover.png",
            slug="recipe-1-name",
        ),
        "recipe-2-uid": Recipe(
            uid="recipe-2-uid",
            name="Recipe 2 Name",
            ingredients="Recipe 2 ingredients edited",
            directions="Recipe 2 description edited",
            description="Recipe 2 description edited",
            notes="Recipe 2 notes edited",
            nutritional_info="Recipe 2 calories edited",
            servings="Recipe 2 servings edited",
            difficulty="Recipe 2 difficulty edited",
            prep_time="Recipe 2 prep time edited",
            cook_time="Recipe 2 cook time edited",
            total_time="Recipe 2 total time edited",
            source="Recipe 2 source edited",
            source_url="https://example.net/recipe-2-source-url-edited",
            image_url=None,
            photo="recipe-2-photo-edited.png",
            photo_hash="recipe-2-photo-hash-edited",
            photo_large="recipe-2-photo-large-edited.png",
            scale="Recipe 2 scale edited",
            hash="recipe-2-hash-edited",
            categories="[]",
            rating=0,
            in_trash=False,
            is_pinned=False,
            on_favorites=False,
            on_grocery_list=False,
            created=datetime(2000, 1, 1, 5, 0, 0),
            photo_url="src/tests/fixtures/photos/photo-2-cover-edited.png",
            slug="recipe-2-name",
        ),
        "recipe-4-uid": Recipe(
            uid="recipe-4-uid",
            name="Recipe 4 Name",
            ingredients="Recipe 4 ingredients",
            directions="Recipe 4 description",
            description="Recipe 4 description",
            notes="Recipe 4 notes",
            nutritional_info="Recipe 4 calories",
            servings="Recipe 4 servings",
            difficulty="Recipe 4 difficulty",
            prep_time="Recipe 4 prep time",
            cook_time="Recipe 4 cook time",
            total_time="Recipe 4 total time",
            source="Recipe 4 source",
            source_url="https://example.net/recipe-4-source-url",
            image_url=None,
            photo="recipe-4-photo.png",
            photo_hash="recipe-4-photo-hash",
            photo_large="recipe-4-photo-large.png",
            scale="Recipe 4 scale",
            hash="recipe-4-hash",
            categories="[]",
            rating=0,
            in_trash=False,
            is_pinned=False,
            on_favorites=False,
            on_grocery_list=False,
            created=datetime(2000, 1, 1, 5, 0, 0),
            photo_url="src/tests/fixtures/photos/photo-4-cover.png",
            slug="recipe-4-name",
        ),
    }
    return response_0, response_1, response_2


@pytest.fixture
def photos():
    response_0 = {}
    response_1 = {
        "photo-1-uid": Photo(
            uid="photo-1-uid",
            filename="photo-1-uid.png",
            recipe_uid="recipe-2-uid",
            order_flag=1,
            name="1",
            hash="photo-1-hash",
            photo_url="src/tests/fixtures/photos/photo-1.png",
        ),
        "photo-2-uid": Photo(
            uid="photo-2-uid",
            filename="photo-2-uid.png",
            recipe_uid="recipe-2-uid",
            order_flag=2,
            name="2",
            hash="photo-2-hash",
            photo_url="src/tests/fixtures/photos/photo-2.png",
        ),
        "photo-3-uid": Photo(
            uid="photo-3-uid",
            filename="photo-3-uid.png",
            recipe_uid="recipe-2-uid",
            order_flag=3,
            name="3",
            hash="photo-3-hash",
            photo_url="src/tests/fixtures/photos/photo-3.png",
        ),
    }
    response_2 = {
        "photo-1-uid": Photo(
            uid="photo-1-uid",
            filename="photo-1-uid.png",
            recipe_uid="recipe-2-uid",
            order_flag=1,
            name="1",
            hash="photo-1-hash",
            photo_url="src/tests/fixtures/photos/photo-1.png",
        ),
        "photo-2-uid": Photo(
            uid="photo-2-uid",
            filename="photo-2-uid.png",
            recipe_uid="recipe-2-uid",
            order_flag=2,
            name="2",
            hash="photo-2-hash-edited",
            photo_url="src/tests/fixtures/photos/photo-2-edited.png",
        ),
        "photo-4-uid": Photo(
            uid="photo-4-uid",
            filename="photo-4-uid.png",
            recipe_uid="recipe-2-uid",
            order_flag=4,
            name="4",
            hash="photo-4-hash",
            photo_url="src/tests/fixtures/photos/photo-4.png",
        ),
    }
    return response_0, response_1, response_2


@pytest.fixture
def categories():
    response_0 = {}
    response_1 = {
        "category-1-uid": Category(
            uid="category-1-uid",
            order_flag=0,
            name="Category 1 Name",
            parent_uid=None,
            icon=None,
            slug="category-1-name",
        ),
        "category-2-uid": Category(
            uid="category-2-uid",
            order_flag=0,
            name="Category 2 Name",
            parent_uid=None,
            icon=None,
            slug="category-2-name",
        ),
        "category-3-uid": Category(
            uid="category-3-uid",
            order_flag=0,
            name="Category 3 Name",
            parent_uid=None,
            icon=None,
            slug="category-3-name",
        ),
        "category-5-uid": Category(
            uid="category-5-uid",
            order_flag=0,
            name="Category 5 Name",
            parent_uid="category-1-uid",
            icon=None,
            slug="category-5-name",
        ),
    }
    response_2 = {
        "category-1-uid": Category(
            uid="category-1-uid",
            order_flag=0,
            name="Category 1 Name",
            parent_uid=None,
            icon=None,
            slug="category-1-name",
        ),
        "category-2-uid": Category(
            uid="category-2-uid",
            order_flag=0,
            name="Category 2 Name Edited",
            parent_uid=None,
            icon=None,
            slug="category-2-name-edited",
        ),
        "category-4-uid": Category(
            uid="category-4-uid",
            order_flag=0,
            name="Category 4 Name",
            parent_uid=None,
            icon=None,
            slug="category-4-name",
        ),
        "category-5-uid": Category(
            uid="category-5-uid",
            order_flag=0,
            name="Category 5 Name",
            parent_uid="category-2-uid",
            icon=None,
            slug="category-5-name",
        ),
    }
    return response_0, response_1, response_2


@pytest.mark.integration
def test_sync_categories(categories):
    response_0, response_1, response_2 = categories

    def compare(response):
        categories = Category.select()
        assert categories.count() == len(response)
        for category in categories:
            observed_category = category.__dict__["__data__"]
            expected_category = response[category.uid].__dict__["__data__"]

            observed_time_created = observed_category.pop("time_created")
            observed_time_updated = observed_category.pop("time_updated")
            expected_category.pop("time_created")

            assert observed_time_updated > observed_time_created
            assert observed_category == expected_category

    compare(response_0)

    sync_categories()
    compare(response_1)

    with patch(
        "src.paprika.PaprikaMockClient._response_folder",
        PAPRIKA_BASE_DIR / "tests" / "fixtures" / "response_2",
    ):
        sync_categories()
    compare(response_2)


@pytest.mark.integration
def test_sync_recipes(recipes):
    from src.paprika import _IMAGE_DIR

    response_0, response_1, response_2 = recipes

    def compare(response):
        recipes = Recipe.select()
        assert recipes.count() == len(response)
        for recipe in recipes:
            observed_recipe = recipe.__dict__["__data__"]
            expected_recipe = response[recipe.uid].__dict__["__data__"]

            observed_time_created = observed_recipe.pop("time_created")
            observed_time_updated = observed_recipe.pop("time_updated")
            expected_recipe.pop("time_created", None)

            assert observed_time_updated > observed_time_created
            assert observed_recipe == expected_recipe

    compare(response_0)
    assert set() == set(_IMAGE_DIR.iterdir())

    sync_recipes()
    compare(response_1)
    assert {
        _IMAGE_DIR / "photo-1.png",
        _IMAGE_DIR / "photo-2.png",
        _IMAGE_DIR / "photo-3.png",
        _IMAGE_DIR / "photo-1-cover.png",
        _IMAGE_DIR / "photo-2-cover.png",
        _IMAGE_DIR / "photo-3-cover.png",
    } == set(_IMAGE_DIR.iterdir())

    with (
        patch(
            "src.paprika.PaprikaMockClient._response_folder",
            PAPRIKA_BASE_DIR / "tests" / "fixtures" / "response_2",
        ),
    ):
        sync_recipes()
    compare(response_2)
    assert {
        _IMAGE_DIR / "photo-1.png",
        _IMAGE_DIR / "photo-2-edited.png",
        _IMAGE_DIR / "photo-4.png",
        _IMAGE_DIR / "photo-1-cover.png",
        _IMAGE_DIR / "photo-2-cover-edited.png",
        _IMAGE_DIR / "photo-4-cover.png",
    } == set(_IMAGE_DIR.iterdir())


@pytest.mark.integration
def test_sync_photos(photos):
    from src.paprika import _IMAGE_DIR

    response_0, response_1, response_2 = photos

    def compare(response):
        photos = Photo.select()
        assert photos.count() == len(response)
        for photo in photos:
            observed_photo = photo.__dict__["__data__"]
            expected_photo = response[photo.uid].__dict__["__data__"]

            observed_time_created = observed_photo.pop("time_created")
            observed_time_updated = observed_photo.pop("time_updated")
            expected_photo.pop("time_created", None)

            assert observed_time_updated > observed_time_created
            assert observed_photo == expected_photo

    compare(response_0)
    assert set() == set(_IMAGE_DIR.iterdir())

    sync_photos()
    compare(response_1)
    assert {
        _IMAGE_DIR / "photo-1.png",
        _IMAGE_DIR / "photo-2.png",
        _IMAGE_DIR / "photo-3.png",
    } == set(_IMAGE_DIR.iterdir())

    with patch(
        "src.paprika.PaprikaMockClient._response_folder",
        PAPRIKA_BASE_DIR / "tests" / "fixtures" / "response_2",
    ):
        sync_photos()
    compare(response_2)
    assert {
        _IMAGE_DIR / "photo-1.png",
        _IMAGE_DIR / "photo-2-edited.png",
        _IMAGE_DIR / "photo-4.png",
    } == set(_IMAGE_DIR.iterdir())
