#!/usr/bin/env python3
import logging
import os
from datetime import timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from peewee import fn
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import MAINTENANCE_FILE, STATIC_DIR, Config, Environment
from src.database import initialize_db
from src.paprika import Category, CategoryRecipe, Recipe, RecipeStatus
from src.render import ingredients, markdown

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


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nDisallow: /\n"


@app.get("/r/{slug}", response_class=HTMLResponse)
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

        zone_info = ZoneInfo(Config.paprika.timezone)

        utc_time_created = recipe.created.replace(tzinfo=timezone.utc)
        local_time_created = utc_time_created.astimezone(zone_info)
        recipe.created = local_time_created.strftime("%B %-d, %Y")

        if recipe.time_updated is None:
            recipe.time_updated = recipe.created
        else:
            utc_time_updated = recipe.time_updated.replace(tzinfo=timezone.utc)
            local_time_updated = utc_time_updated.astimezone(zone_info)
            if local_time_updated < local_time_created:
                # address timezone adjustment due to travel or daylight savings
                recipe.time_updated = recipe.created
            else:
                recipe.time_updated = local_time_updated.strftime("%B %-d, %Y")

        response["recipe"] = recipe
        for attribute in Recipe.markdown_fields:
            content = getattr(recipe, attribute)
            if attribute == "ingredients":
                setattr(
                    recipe,
                    attribute,
                    ingredients(recipe.uid, content),
                )
            else:
                setattr(
                    recipe,
                    attribute,
                    markdown(recipe.uid, content),
                )
    except Recipe.DoesNotExist:
        return templates.TemplateResponse(
            "404.html", {"request": request, "response": response}
        )
    return templates.TemplateResponse(
        "recipe.html",
        {"request": request, "response": response, "page_title": recipe.name},
    )


@app.get("/", response_class=HTMLResponse)
@app.get("/c/{slug}", response_class=HTMLResponse)
async def index(request: Request, slug: str | None = None):
    recipes = (
        Recipe.select()
        .where(Recipe.in_trash == 0)
        .order_by(
            fn.MAX(
                fn.COALESCE(Recipe.time_updated, Recipe.created), Recipe.created
            ).desc()
        )
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
                "photo_large": recipe.photo_large,
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
