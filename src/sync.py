#!/usr/bin/env python3
"""
Usage:
    ./%(script_name)s [--force] [--limit=<n>]
    ./%(script_name)s categories [--force]
    ./%(script_name)s recipes [--force] [--limit=<n>]
    ./%(script_name)s recipe --uid=<uid> [--force] [--limit=<n>]
    ./%(script_name)s photos [--force]
    ./%(script_name)s photo --uid=<uid> [--force]

Options:
    -h --help           Show this screen.
    --force             Force sync even if the hash is the same.
    --limit=<n>         Limit the number of records to add or update per record
                            type.
    --uid=<uid>         The uid of the recipe or photo to sync.

Examples:
    # Sync everything
    ./%(script_name)s

    # Sync categories
    ./%(script_name)s categories

    # Sync recipes including the cover photo
    ./%(script_name)s recipes

    # Sync a recipe including the cover photo
    ./%(script_name)s recipe --uid=1

    # Sync recipes without non-cover photos
    ./%(script_name)s recipes

    # Sync a recipe without non-cover photos
    ./%(script_name)s recipe --uid=2

    # Sync photos
    ./%(script_name)s photos

    # Sync a photo
    ./%(script_name)s photo --uid=3
"""

import logging
import sys
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

from docopt import docopt
from huey import crontab
from peewee import IntegrityError

from src.app import huey
from src.database import initialize_db
from src.paprika import (
    Category,
    CategoryRecipe,
    DoesNotExistError,
    PaprikaClient,
    Photo,
    Recipe,
)

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

__doc__ %= {
    "script_name": Path(__file__).name,
}


class Stats(NamedTuple):
    added: int = 0
    updated: int = 0
    deleted: int = 0

    def __add__(self, other):
        if not isinstance(other, Stats):
            return NotImplementedError
        return Stats(
            added=self.added + other.added,
            updated=self.updated + other.updated,
            deleted=self.deleted + other.deleted,
        )


def sync_photo(uid: str, force: bool = False, **kwargs) -> Stats:
    logger.debug(f"Syncing Photo record: {uid}")
    try:
        with PaprikaClient.get() as client:
            paprika_photo = client.get_photo(uid)
    except DoesNotExistError:
        paprika_photo = None
    db_photo = Photo.get_or_none(uid=uid)

    deleted = 0
    if not paprika_photo:
        if db_photo:
            with PaprikaClient.get() as client:
                client.delete_photo(db_photo.photo_url)
            db_photo.delete_instance()
            logger.debug(f"Deleted Photo record: {uid}")
            deleted += 1
        return Stats(deleted=deleted)

    with PaprikaClient.get() as client:
        client.save_photo(paprika_photo.photo_url)

    added, updated = 0, 0
    if db_photo:
        if paprika_photo.hash != db_photo.hash or force:
            paprika_parsed_url = urlparse(paprika_photo.photo_url)
            db_parsed_url = urlparse(db_photo.photo_url)
            if (
                Path(paprika_parsed_url.path).name
                != Path(db_parsed_url.path).name
            ):
                with PaprikaClient.get() as client:
                    client.delete_photo(db_photo.photo_url)
            db_photo.update_from_dict(
                **(paprika_photo.__data__ | kwargs | {"uid": uid})
            )
            db_photo.save()
            logger.debug(f"Updated Photo record: {uid}")
            updated += 1
    else:
        paprika_photo.update_from_dict(**(kwargs | {"uid": uid}))
        paprika_photo.save(force_insert=True)
        logger.debug(f"Saved Photo record: {uid}")
        added += 1

    return Stats(added=added, updated=updated, deleted=deleted)


def sync_photos(
    recipe_uid: str | list[str] | None = None, force: bool = False
) -> Stats:
    if not recipe_uid:
        recipe_uid = []
    elif isinstance(recipe_uid, str):
        recipe_uid = [recipe_uid]

    if recipe_uid:
        logger.debug(f"Syncing Photo records for Recipes: {recipe_uid}")
    else:
        logger.debug("Syncing Photo records")

    with PaprikaClient.get() as client:
        paprika_photos = client.get_photos()

    db_photos = Photo.select()
    if recipe_uid:
        db_photos = db_photos.where(Photo.recipe_uid.in_(recipe_uid))

    db_photo_uids_to_hash = {photo.uid: photo.hash for photo in db_photos}
    paprika_photo_uids_to_hash = {
        photo.uid: photo.hash
        for photo in paprika_photos
        if not recipe_uid or photo.recipe_uid in recipe_uid
    }

    stats = Stats()

    uids_to_delete = set(db_photo_uids_to_hash.keys()) - set(
        paprika_photo_uids_to_hash.keys()
    )
    for uid in uids_to_delete:
        stats += sync_photo(uid=uid)

    for photo in paprika_photos:
        if recipe_uid and photo.recipe_uid not in recipe_uid:
            continue
        if photo.hash != db_photo_uids_to_hash.get(photo.uid) or force:
            stats += sync_photo(force=force, **photo.__data__)

    return stats


def sync_category_recipes(recipe_uid: str, category_uids: list[str]) -> None:
    logger.debug(f"Syncing CategoryRecipe records for Recipe: {recipe_uid}")
    num_deleted = (
        CategoryRecipe.delete()
        .where(
            CategoryRecipe.recipe
            == recipe_uid & ~CategoryRecipe.category.in_(category_uids)
        )
        .execute()
    )
    if num_deleted > 0:
        logger.debug(f"Deleted CategoryRecipe records: {category_uids}")

    db_category_recipe_category_uids = [
        category_recipe.category.uid
        for category_recipe in CategoryRecipe.select().where(
            CategoryRecipe.recipe == recipe_uid
        )
    ]
    for category_uid in category_uids:
        if category_uid not in db_category_recipe_category_uids:
            try:
                CategoryRecipe.create(
                    recipe=recipe_uid, category=category_uid
                ).save()
                logger.debug(
                    f"Added CategoryRecipe record: {recipe_uid=}, "
                    f"{category_uid=}"
                )
            except IntegrityError:
                if "FOREIGN KEY constraint failed" in str(sys.exc_info()[1]):
                    category = Category.get_or_none(uid=category_uid)
                    if not category:
                        # From recipe: 3019849D-8296-46EE-B3FC-1D8DE548BC4E
                        logger.warning(f"Unknown category: {category_uid}")
                        continue
                raise


def sync_recipe(uid: str, force: bool = False, **kwargs):
    logger.debug(f"Syncing Recipe record: {uid}")
    try:
        with PaprikaClient.get() as client:
            paprika_recipe = client.get_recipe(uid)
    except DoesNotExistError:
        paprika_recipe = None
    db_recipe = Recipe.get_or_none(uid=uid)

    sync_photos(recipe_uid=uid, force=force)

    deleted = 0
    if not paprika_recipe:
        if db_recipe:
            with PaprikaClient.get() as client:
                client.delete_photo(db_recipe.photo_url)
            db_recipe.delete_instance()
            logger.debug(f"Deleted Recipe record: {db_recipe.name}")
            deleted += 1
        return

    if paprika_recipe.photo_url:
        with PaprikaClient.get() as client:
            client.save_photo(paprika_recipe.photo_url)

    if db_recipe:
        if paprika_recipe.hash != db_recipe.hash or force:
            paprika_parsed_url = urlparse(paprika_recipe.photo_url)
            db_parsed_url = urlparse(db_recipe.photo_url)
            if (
                paprika_parsed_url.path
                and Path(paprika_parsed_url.path).name
                != Path(db_parsed_url.path).name
            ):
                with PaprikaClient.get() as client:
                    client.delete_photo(db_recipe.photo_url)
            db_recipe.update_from_dict(**(paprika_recipe.__data__ | kwargs))
            db_recipe.save()
            logger.debug(f"Updated Recipe record: {db_recipe.name}")
    else:
        paprika_recipe.update_from_dict(**(kwargs | {"uid": uid}))
        paprika_recipe.save(force_insert=True)
        logger.debug(f"Saved Recipe record: {paprika_recipe.name}")

    sync_category_recipes(
        recipe_uid=uid, category_uids=paprika_recipe.categories
    )


def sync_recipes(force: bool = False, limit: int | None = None):
    logger.debug("Syncing Recipe records")
    with PaprikaClient.get() as client:
        paprika_recipes = client.get_recipes()
    db_recipes = Recipe.select()

    db_recipe_uids_to_hash = {recipe.uid: recipe.hash for recipe in db_recipes}
    paprika_recipe_uids_to_hash = {
        recipe.uid: recipe.hash for recipe in paprika_recipes
    }
    uids_to_delete = set(db_recipe_uids_to_hash.keys()) - set(
        paprika_recipe_uids_to_hash.keys()
    )
    if uids_to_delete:
        for uid in uids_to_delete:
            sync_recipe(uid=uid, force=force)

    i = 0
    for recipe in paprika_recipes:
        if recipe.hash != db_recipe_uids_to_hash.get(recipe.uid) or force:
            sync_recipe(force=force, **recipe.__data__)
            i += 1

        if limit and i == limit:
            break


def sync_categories(force: bool = False):
    logger.debug("Syncing Category records")
    with PaprikaClient.get() as client:
        paprika_categories = client.get_categories()
    db_categories = Category.select()

    db_category_by_uid = {category.uid: category for category in db_categories}
    paprika_category_by_uid = {
        category.uid: category for category in paprika_categories
    }
    uids_to_delete = set(db_category_by_uid.keys()) - set(
        paprika_category_by_uid.keys()
    )
    if uids_to_delete:
        Category.delete().where(Category.uid.in_(uids_to_delete)).execute()
        logger.debug(f"Deleted Category records: {uids_to_delete}")

    for paprika_category in paprika_categories:
        if paprika_category.uid in db_category_by_uid:
            if (
                paprika_category.hash
                == db_category_by_uid.get(paprika_category.uid).hash
                and not force
            ):
                continue
            db_category = db_category_by_uid.get(paprika_category.uid)
            db_category.update_from_dict(**(paprika_category.__data__))
            db_category.save()
            logger.debug(f"Updated Category record: {paprika_category.uid}")
        else:
            paprika_category.save(force_insert=True)
            logger.debug(f"Saved Category record: {paprika_category.uid}")


def sync_all(force: bool = False, limit: int | None = None):
    sync_categories(force=force)
    sync_recipes(force=force, limit=limit)


@huey.task(crontab(minute="0"))
def schedule_sync():
    sync_all()


def main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv[1:]

    args = docopt(__doc__, argv=argv)
    force = bool(args.get("--force"))
    limit = int(args.get("--limit")) if args.get("--limit") else None
    categories = args.get("categories")
    recipes = args.get("recipes")
    recipe = args.get("recipe")
    uid = args.get("--uid")
    photos = args.get("photos")
    photo = args.get("photo")

    if categories:
        sync_categories(force=force)
    elif recipes:
        sync_recipes(force=force, limit=limit)
    elif recipe:
        sync_recipe(uid=uid, force=force, limit=limit)
    elif photos:
        sync_photos(force=force)
    elif photo:
        sync_photo(uid=uid, force=force)
    else:
        sync_all(force=force, limit=limit)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    initialize_db()
    main()
