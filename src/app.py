#!/usr/bin/env python3
import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from huey import RedisHuey
from peewee import fn
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import MAINTENANCE_FILE, STATIC_DIR, Config, Environment
from src.database import initialize_db, redis_pool
from src.paprika import Category, CategoryRecipe, Recipe, RecipeStatus
from src.render import markdown

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

initialize_db()

_BASE_DIR = Path(__file__).parent


class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if os.path.exists(MAINTENANCE_FILE):
            return templates.TemplateResponse("503.html", {"request": request})
        return await call_next(request)


app = FastAPI()
app.add_middleware(MaintenanceMiddleware)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=_BASE_DIR / "templates")

huey = RedisHuey(Config.project_name, connection_pool=redis_pool())


def base():
    return {
        "title": Config.title,
        "email": Config.email,
        "categories": {
            category.name: category.slug
            for category in Category.select()
            if (
                Category.parent_uid.is_null()
                and (
                    category.name in Config.paprika.listed_categories
                    or (
                        not Config.paprika.listed_categories
                        and category.name
                        not in Config.paprika.hidden_categories
                        and category.name
                        not in Config.paprika.secret_categories
                    )
                )
            )
        },
    }


@app.get("/r/{slug}")
async def recipe(request: Request, slug: str):
    response = base()
    try:
        recipe = [
            recipe
            for recipe in Recipe.select().where(Recipe.slug == slug)
            if recipe.status == RecipeStatus.LISTED and not recipe.trashed
        ]
        if len(recipe) > 1:
            raise Recipe.DoesNotExist
        else:
            recipe = recipe[0]

        recipe.created = recipe.created.strftime("%B %d, %Y")
        recipe.time_updated = recipe.time_updated.strftime("%B %d, %Y")
        response["recipe"] = recipe
        for attribute in Recipe.markdown_fields:
            setattr(
                recipe,
                attribute,
                markdown(recipe.uid, getattr(recipe, attribute)),
            )
    except Recipe.DoesNotExist:
        return templates.TemplateResponse(
            "404.html", {"request": request, "response": response}
        )
    return templates.TemplateResponse(
        "recipe.html",
        {"request": request, "response": response, "page_title": recipe.name},
    )


@app.get("/")
@app.get("/c/{slug}")
async def index(request: Request, slug: str | None = None):
    recipes = (
        Recipe.select()
        .where(Recipe.in_trash == 0)
        .order_by(Recipe.time_updated.desc())
    )

    if slug:
        category = Category.select().where(Category.slug == slug)
        if category.count() > 1:
            logger.warning("Multiple categories found with the same slug")
            return templates.TemplateResponse(
                "404.html", {"request": request, "response": base()}
            )
        else:
            category = category.get()

        recipes = recipes.join(
            CategoryRecipe, on=(Recipe.uid == CategoryRecipe.recipe)
        ).where(CategoryRecipe.category == category)

    recipes = recipes.group_by(Recipe.slug)

    if multi_recipes := recipes.having(fn.Count(Recipe.uid) > 1):
        for recipe in multi_recipes:
            logger.warning(
                f"More than one recipe found with slug {recipe.slug}"
            )
        recipes = recipes.having(fn.Count(Recipe.uid) == 1)

    response = base()
    response["recipes"] = []
    for recipe in recipes:
        if recipe.status not in [RecipeStatus.LISTED, RecipeStatus.SECRET]:
            continue
        if set(Config.paprika.hidden_categories) & {
            category.name for category in recipe.categories_list
        }:
            continue
        response["recipes"].append(
            {
                "name": recipe.name,
                "slug": recipe.slug,
                "rating": recipe.rating,
                "photo_filename": recipe.photo_filename,
                "secret": recipe.status == RecipeStatus.SECRET,
            }
        )
    return templates.TemplateResponse(
        "gallery.html", {"request": request, "response": response}
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=Config.environment == Environment.LOCAL,
    )
