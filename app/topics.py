from pydantic import BaseModel

from app.domain import Topic
from app.llm import INVALID_OUTPUT, LLMError, StructuredLLM
from app.syllabus import split_topics

MIN_LENGTH = 3

SYSTEM_PROMPT = (
    "Extraés los contenidos que se enseñan en el programa de una materia universitaria. "
    "Recibís el texto crudo de un PDF o Word, que puede traer encabezados, nombres de docentes, carga horaria, "
    "correlativas, bibliografía, números de página, viñetas rotas y palabras cortadas por la extracción. "
    "Devolvé solo los temas de contenido, uno por elemento, con sus palabras originales y corrigiendo cortes de palabras. "
    "Si una unidad tiene subtemas, devolvé cada subtema como un tema aparte. "
    "No inventes temas. Ignorá objetivos, metodología, evaluación, bibliografía y datos administrativos."
)


class TopicList(BaseModel):
    topics: list[str]


def unique_topics(names: list[str]) -> list[Topic]:
    seen: dict[str, str] = {}
    for name in (item.strip() for item in names):
        if len(name) >= MIN_LENGTH:
            seen.setdefault(name.lower(), name)
    return [Topic(index=index, text=text) for index, text in enumerate(seen.values())]


def require_topics(result: TopicList) -> None:
    if not unique_topics(result.topics):
        raise ValueError("The model returned no topics")


class TopicExtractor:
    def __init__(self, llm: StructuredLLM) -> None:
        self._llm = llm

    def extract(self, text: str) -> list[Topic]:
        try:
            return unique_topics(self._llm.ask(SYSTEM_PROMPT, text, TopicList, check=require_topics).topics)
        except LLMError as error:
            if error.code != INVALID_OUTPUT:
                raise
            return split_topics(text)
