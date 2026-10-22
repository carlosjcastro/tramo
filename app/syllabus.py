import re

from app.domain import Topic
from app.noise import is_noise

UNIT_HEADER = re.compile(r"^\s*(unidad|tema|m[oó]dulo)\s*\w*\s*[:.)\-\u2013\u2014]\s*", re.IGNORECASE)
BULLETS = re.compile(r"^[\s•●▪■□▯◦·*■-◿-]+")
NUMBERING = re.compile(r"^\(?\d+(\.\d+)*[.)]?\s+")
BIBLIOGRAPHY = re.compile(r"\bbibliograf[ií]a\b", re.IGNORECASE)
TRAILING_NUMBER = re.compile(r"\s+\d+(\.\d+)+$")
SPLITTER = re.compile(r"(?<=[.;])(?<!\bvs\.)(?<!\bej\.)\s+|\n+")
PUNCTUATION = " .;:\t"
MIN_LENGTH = 3
BIBLIOGRAPHY_FROM = 0.6


def drop_bibliography(text: str) -> str:
    for match in BIBLIOGRAPHY.finditer(text):
        if match.start() >= len(text) * BIBLIOGRAPHY_FROM:
            return text[: match.start()]
    return text


def clean_topic(chunk: str) -> str:
    text = BULLETS.sub("", chunk)
    text = UNIT_HEADER.sub("", text)
    text = NUMBERING.sub("", text)
    return TRAILING_NUMBER.sub("", text.strip(PUNCTUATION)).strip(PUNCTUATION)


def split_topics(text: str) -> list[Topic]:
    unique: dict[str, str] = {}
    for chunk in SPLITTER.split(drop_bibliography(text)):
        topic = clean_topic(chunk)
        if len(topic) >= MIN_LENGTH and not is_noise(topic):
            unique.setdefault(topic.lower(), topic)
    return [Topic(index=index, text=topic) for index, topic in enumerate(unique.values())]
