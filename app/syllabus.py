import re

from app.domain import Topic

UNIT_HEADER = re.compile(r"^\s*(unidad|tema|m[oó]dulo)\s*\w*\s*[:.)]\s*", re.IGNORECASE)
SPLITTER = re.compile(r"(?<=[.;])\s+|\n+")
MIN_LENGTH = 3


def split_topics(text: str) -> list[Topic]:
    parts = (UNIT_HEADER.sub("", chunk).strip(" .;:\t") for chunk in SPLITTER.split(text))
    return [Topic(index=i, text=part) for i, part in enumerate(p for p in parts if len(p) >= MIN_LENGTH)]
