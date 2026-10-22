from typing import Iterator

from app.advisor import Advisor
from app.assessment import TopicAssessor
from app.domain import Progress, Report, TopicMatch
from app.policy import EquivalencePolicy
from app.sanitize import clean_input, looks_like_injection
from app.topics import Extraction, TopicExtractor

EXTRACT_UNITS = 1
BATCH_UNITS = 2
ADVISE_UNITS = 1
NO_TOPICS = (
    "No se detectaron temas en uno de los programas. "
    "Revisá que el texto tenga contenidos separados por líneas o por punto y coma."
)
INJECTION_WARNING = (
    "Uno de los programas contiene frases que parecen instrucciones dirigidas a la IA. "
    "Se trataron como texto del programa, pero revisá el informe con más cuidado."
)
FALLBACK_WARNING = (
    "La IA no pudo devolver los temas de uno de los programas en el formato esperado, "
    "así que se usó un método por reglas. Revisá que los temas del informe sean los correctos."
)


class ProgressTracker:
    def __init__(self) -> None:
        self.done = 0
        self.total = 2 * EXTRACT_UNITS + BATCH_UNITS + ADVISE_UNITS

    def plan(self, batches: int) -> None:
        self.total = 2 * EXTRACT_UNITS + batches * BATCH_UNITS + ADVISE_UNITS

    def advance(self, units: int) -> None:
        self.done += units

    def event(self, stage: str, current: int = 0, count: int = 0) -> Progress:
        return Progress(done=self.done, total=self.total, stage=stage, current=current, count=count)


class EquivalenceService:
    def __init__(
        self,
        extractor: TopicExtractor,
        assessor: TopicAssessor,
        advisor: Advisor,
        policy: EquivalencePolicy,
        model: str,
    ) -> None:
        self._extractor = extractor
        self._assessor = assessor
        self._advisor = advisor
        self._policy = policy
        self._model = model

    def analyze(self, source_text: str, target_text: str) -> Report:
        *_, report = self.analyze_events(source_text, target_text)
        return report

    def analyze_events(self, source_text: str, target_text: str) -> Iterator[Progress | Report]:
        tracker = ProgressTracker()
        yield tracker.event("extracting_origin")
        origin = self._extractor.extract(source_text)
        tracker.advance(EXTRACT_UNITS)
        yield tracker.event("extracting_target")
        destination = self._extractor.extract(target_text)
        tracker.advance(EXTRACT_UNITS)
        if not origin.topics or not destination.topics:
            raise ValueError(NO_TOPICS)
        matches = yield from self._assess(origin, destination, tracker)
        report = self._policy.evaluate(matches)
        yield tracker.event("advising")
        recommendation = self._advisor.recommend(report)
        tracker.advance(ADVISE_UNITS)
        yield tracker.event("finished")
        warnings = self._warnings(source_text, target_text, origin, destination)
        yield report.model_copy(update={"recommendation": recommendation, "model": self._model, "warnings": warnings})

    def recompute(self, matches: list[TopicMatch]) -> Report:
        return self._policy.evaluate(matches).model_copy(update={"model": self._model})

    def _assess(
        self, origin: Extraction, destination: Extraction, tracker: ProgressTracker
    ) -> Iterator[Progress | list[TopicMatch]]:
        count = self._assessor.batch_count(len(destination.topics))
        tracker.plan(count)
        matches: list[TopicMatch] = []
        yield tracker.event("assessing", 1, count)
        for number, batch in enumerate(self._assessor.assess_batches(origin.topics, destination.topics), 1):
            matches += batch
            tracker.advance(BATCH_UNITS)
            if number < count:
                yield tracker.event("assessing", number + 1, count)
        return matches

    def _warnings(self, source_text: str, target_text: str, origin: Extraction, destination: Extraction) -> list[str]:
        warnings = []
        if looks_like_injection(clean_input(f"{source_text}\n{target_text}")):
            warnings.append(INJECTION_WARNING)
        if not (origin.by_model and destination.by_model):
            warnings.append(FALLBACK_WARNING)
        return warnings
