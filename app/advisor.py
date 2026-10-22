import re

from pydantic import BaseModel

from app.domain import Report, Status, Verdict
from app.llm import StructuredLLM

SYSTEM_PROMPT = (
    "Redactás una recomendación breve para el docente que debe informar una solicitud de equivalencia de materias. "
    "Los números y el veredicto ya fueron calculados por reglas del reglamento y no podés cambiarlos ni discutirlos. "
    "Escribí entre tres y cinco oraciones en español: qué sugiere la evidencia, qué temas conviene revisar primero "
    "y qué dudas o riesgos tiene la comparación. Agrupá los temas sin evidencia en bloques temáticos y mencioná primero "
    "los bloques más grandes, describiendo su peso con palabras como la mayor parte o un bloque amplio, antes de los temas parciales. "
    "No escribas cantidades ni porcentajes, porque el informe ya los muestra. "
    "No inventes artículos ni temas. "
    "Recordá que el docente decide y el Consejo Directivo resuelve."
)

VERDICT_TEXT = {
    Verdict.total: "equivalencia total",
    Verdict.partial: "equivalencia parcial, porque más del 50% del programa de destino tiene equivalente",
    Verdict.insufficient: "evidencia insuficiente, porque la cobertura no supera el 50% del programa de destino",
}

STATUS_TEXT = {Status.covered: "cubierto", Status.partial: "parcial", Status.missing: "sin evidencia"}


SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")
NUMBER = re.compile(r"\d+")
CITED_ARTICLES = {50, 87, 88}


class Recommendation(BaseModel):
    recommendation: str


def allowed_numbers(report: Report) -> set[int]:
    counts = {sum(match.status is status for match in report.matches) for status in Status}
    return counts | {round(report.coverage * 100), len(report.matches)} | CITED_ARTICLES


def keep_verified_sentences(text: str, allowed: set[int]) -> str | None:
    sentences = [part for part in SENTENCE_BREAK.split(text.strip()) if part]
    kept = [part for part in sentences if all(int(number) in allowed for number in NUMBER.findall(part))]
    return " ".join(kept) or None


def build_prompt(report: Report) -> str:
    counts = {status: sum(match.status is status for match in report.matches) for status in Status}
    open_topics = [match for match in report.matches if match.status is not Status.covered]
    lines = [
        f"Cobertura calculada: {round(report.coverage * 100)}%",
        f"Veredicto calculado: {VERDICT_TEXT[report.verdict]}",
        f"Cubiertos: {counts[Status.covered]}. Parciales: {counts[Status.partial]}. Sin evidencia: {counts[Status.missing]}.",
        "",
        "Temas no cubiertos del todo, con el motivo de la evaluación:",
        *(f"{number}. {STATUS_TEXT[match.status]}: {match.target.text}. {match.reason}" for number, match in enumerate(open_topics, 1)),
    ]
    return "\n".join(lines)


class Advisor:
    def __init__(self, llm: StructuredLLM) -> None:
        self._llm = llm

    def recommend(self, report: Report) -> str | None:
        text = self._llm.ask(SYSTEM_PROMPT, build_prompt(report), Recommendation).recommendation
        return keep_verified_sentences(text, allowed_numbers(report))
