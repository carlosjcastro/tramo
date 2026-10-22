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
    sources: list[Topic] = []
    status: Status
    reason: str = ""
    overridden: bool = False


class Progress(BaseModel):
    done: int
    total: int
    stage: str
    current: int = 0
    count: int = 0


class Report(BaseModel):
    matches: list[TopicMatch]
    coverage: float = Field(ge=0, le=1)
    verdict: Verdict
    pending_topics: list[str]
    recommendation: str | None = None
    model: str = ""
    warnings: list[str] = []
