from enum import Enum

from pydantic import BaseModel, Field


class Status(str, Enum):
    covered = "cubierto"
    partial = "parcial"
    missing = "sin_evidencia"


class Verdict(str, Enum):
    total = "equivalencia_total"
    partial = "equivalencia_parcial"
    insufficient = "evidencia_insuficiente"


class Topic(BaseModel):
    index: int
    text: str


class TopicMatch(BaseModel):
    target: Topic
    source: Topic | None
    score: float
    status: Status
    evidence: str | None = None


class Report(BaseModel):
    matches: list[TopicMatch]
    coverage: float = Field(ge=0, le=1)
    verdict: Verdict
    pending_topics: list[str]
