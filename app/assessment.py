import re

from pydantic import BaseModel

from app.domain import Status, Topic, TopicMatch
from app.llm import StructuredLLM

SYSTEM_PROMPT = (
    "Ayudás a un docente a revisar una solicitud de equivalencia entre dos materias universitarias. "
    "Recibís la lista numerada de temas del programa de la materia APROBADA (origen) y una lista numerada de temas "
    "de la materia a RECONOCER (destino). Para cada tema de destino decidí con criterio estricto: "
    "cubierto solo si algún tema del origen enseña explícitamente ese mismo contenido con alcance y profundidad "
    "equivalentes; un tema base, previo o relacionado no alcanza para cubierto; "
    "parcial si el origen cubre solo una parte, o el tema de destino exige más profundidad, más herramientas o una "
    "tecnología específica que el origen no menciona; "
    "sin_evidencia si ningún tema del origen corresponde. "
    "Compartir palabras como introducción, avanzado o programación no alcanza. "
    "Citá en source_numbers, como máximo cinco, los números de los temas del origen que mejor respaldan tu decisión, "
    "o una lista vacía si no hay. "
    "Explicá en reason, en una o dos oraciones en español, qué coincide y qué falta, nombrando los temas por su "
    "texto y sin escribir nunca sus números. "
    "Devolvé una evaluación por cada tema de destino, usando su número en target_number."
)


class Assessment(BaseModel):
    target_number: int
    status: Status
    source_numbers: list[int] = []
    reason: str


class AssessmentBatch(BaseModel):
    assessments: list[Assessment]


MAX_SOURCES = 5
NUMBER_REFERENCE = re.compile(r"\s*\((?:temas?\s+)?\d+(?:\s*(?:,|y|a|-|–)\s*\d+)*\)")


def clean_reason(reason: str) -> str:
    return NUMBER_REFERENCE.sub("", reason).strip()


def numbered(topics: list[Topic]) -> str:
    return "\n".join(f"{position}. {topic.text}" for position, topic in enumerate(topics, 1))


def check_batch(batch: AssessmentBatch, sources: int, targets: int) -> None:
    numbers = [item.target_number for item in batch.assessments]
    if sorted(numbers) != list(range(1, targets + 1)):
        raise ValueError("The model must assess every target topic exactly once")
    for item in batch.assessments:
        if any(not 1 <= number <= sources for number in item.source_numbers):
            raise ValueError("The model cited a source topic that does not exist")
        if item.status is not Status.missing and not item.source_numbers:
            raise ValueError("The model must cite sources for covered or partial topics")


class TopicAssessor:
    def __init__(self, llm: StructuredLLM, batch_size: int) -> None:
        self._llm = llm
        self._batch_size = batch_size

    def assess(self, sources: list[Topic], targets: list[Topic]) -> list[TopicMatch]:
        matches: list[TopicMatch] = []
        for start in range(0, len(targets), self._batch_size):
            matches += self._assess_batch(sources, targets[start : start + self._batch_size])
        return matches

    def _assess_batch(self, sources: list[Topic], targets: list[Topic]) -> list[TopicMatch]:
        prompt = f"Temas del origen:\n{numbered(sources)}\n\nTemas de destino:\n{numbered(targets)}"
        result = self._llm.ask(
            SYSTEM_PROMPT,
            prompt,
            AssessmentBatch,
            check=lambda batch: check_batch(batch, len(sources), len(targets)),
        )
        by_number = {item.target_number: item for item in result.assessments}
        return [self._match(topic, by_number[number], sources) for number, topic in enumerate(targets, 1)]

    def _match(self, target: Topic, item: Assessment, sources: list[Topic]) -> TopicMatch:
        numbers = list(dict.fromkeys(item.source_numbers))[:MAX_SOURCES]
        cited = [] if item.status is Status.missing else [sources[number - 1] for number in numbers]
        return TopicMatch(target=target, sources=cited, status=item.status, reason=clean_reason(item.reason))
