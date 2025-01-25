import re

from markdown import markdown as _markdown

from src.paprika import Photo

_TEMPLATE = "[photo:{name}]"


def markdown(recipe_uid: int, content: str) -> str:
    pattern = r"\[photo:(\d+)\]"
    photo_names = re.findall(pattern, content)

    if photo_names:
        photos = Photo.select().where(Photo.recipe_uid == recipe_uid)
        photo_html = {
            photo.name: f'<img src="/static/images/{photo.filename}">'
            for photo in photos
        }
        for name in photo_names:
            search = _TEMPLATE.format(name=name)
            content = content.replace(search, photo_html.get(name, search))

    return _markdown(content, extensions=["nl2br"])
