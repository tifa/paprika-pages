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


def ingredients(recipe_uid: int, content: str) -> str:
    integer = r"\d+"
    decimal = r"\d+\.\d+"
    ascii_fraction = r"\d+/\d+"
    mixed_fraction = r"\d+\s+\d+/\d+"
    unicode_fraction = r"[\u00BC-\u00BE\u2150-\u215E]"
    single_number = (
        rf"(?:{mixed_fraction}|{ascii_fraction}|{decimal}|{integer}|"
        rf"{unicode_fraction})"
    )
    range_number = rf"(?:\s*[-–]\s*{single_number})?"
    pattern_str = rf"^\s*({single_number}{range_number})"
    pattern = re.compile(pattern_str)

    lines = content.splitlines()
    processed_lines = []
    for line in lines:
        if line.startswith("**") and line.endswith("**"):
            if processed_lines:
                processed_lines.append("</ul>")
            processed_line = markdown(recipe_uid, line)
            processed_lines.append(processed_line)
            processed_lines.append("<ul>")
        elif line != "":
            if not processed_lines:
                processed_lines.append("<ul>")
            line = pattern.sub(r"<span>\1</span>", line)
            processed_lines.append(f"<li>{line}</li>")
    if processed_lines:
        processed_lines.append("</ul>")
    return "\n".join(processed_lines)
