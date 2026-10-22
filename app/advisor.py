import re

from pydantic import BaseModel

from app.domain import Report, Status, TopicMatch, Verdict
from app.llm import StructuredLLM

SYSTEM_PROMPT = (
    "Redactás una recomendación breve para el docente que debe informar una solicitud de equivalencia de materias. "
    "Los números y el veredicto ya fueron calculados por reglas del reglamento y no podés cambiarlos ni discutirlos. "
    "Escribí entre tres y cinco oraciones en español: qué sugiere la evidencia, qué temas conviene revisar primero "
    "y qué dudas o riesgos tiene la comparación. Mencioná primero los tramos consecutivos sin evidencia que se indican, "
    "del más largo al más corto, nombrando desde qué tema hasta cuál, y después los temas parciales. "
    "Podés usar las cifras de esos tramos y ninguna otra cantidad ni porcentaje, porque el informe ya los muestra. "
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


MIN_RUN = 3
MAX_RUNS = 3


def missing_runs(matches: list[TopicMatch]) -> list[tuple[str, str, int]]:
    runs: list[list[TopicMatch]] = []
    previous_missing = False
    for match in matches:
        missing = match.status is Status.missing
        if missing and previous_missing:
            runs[-1].append(match)
        elif missing:
            runs.append([match])
        previous_missing = missing
    long_runs = [run for run in runs if len(run) >= MIN_RUN]
    ranked = sorted(long_runs, key=len, reverse=True)[:MAX_RUNS]
    return [(run[0].target.text, run[-1].target.text, len(run)) for run in ranked]


def allowed_numbers(report: Report) -> set[int]:
    counts = {sum(match.status is status for match in report.matches) for status in Status}
    lengths = {length for _, _, length in missing_runs(report.matches)}
    return counts | lengths | {round(report.coverage * 100), len(report.matches)} | CITED_ARTICLES


def keep_verified_sentences(text: str, allowed: set[int]) -> str | None:
    sentences = [part for part in SENTENCE_BREAK.split(text.strip()) if part]
    kept = [part for part in sentences if all(int(number) in allowed for number in NUMBER.findall(part))]
    return " ".join(kept) or None


def build_prompt(report: Report) -> str:
    counts = {status: sum(match.status is status for match in report.matches) for status in Status}
    open_topics = [match for match in report.matches if match.status is not Status.covered]
    runs = missing_runs(report.matches)
    run_lines = (
        [
            "",
            "Tramos consecutivos del programa de destino sin evidencia, del más largo al más corto:",
            *(f"{number}. Desde «{first}» hasta «{last}» ({length} temas)" for number, (first, last, length) in enumerate(runs, 1)),
        ]
        if runs
        else []
    )
    lines = [
        f"Cobertura calculada: {round(report.coverage * 100)}%",
        f"Veredicto calculado: {VERDICT_TEXT[report.verdict]}",
        f"Cubiertos: {counts[Status.covered]}. Parciales: {counts[Status.partial]}. Sin evidencia: {counts[Status.missing]}.",
        "",
        "Temas no cubiertos del todo, con el motivo de la evaluación:",
        *(f"{number}. {STATUS_TEXT[match.status]}: {match.target.text}. {match.reason}" for number, match in enumerate(open_topics, 1)),
        *run_lines,
    ]
    return "\n".join(lines)


class Advisor:
    def __init__(self, llm: StructuredLLM) -> None:
        self._llm = llm

    def recommend(self, report: Report) -> str | None:
        text = self._llm.ask(SYSTEM_PROMPT, build_prompt(report), Recommendation).recommendation
        return keep_verified_sentences(text, allowed_numbers(report))
