from app.advisor import Advisor
from app.assessment import TopicAssessor
from app.domain import Report, TopicMatch
from app.policy import EquivalencePolicy
from app.sanitize import clean_input, looks_like_injection
from app.topics import TopicExtractor


INJECTION_WARNING = (
    "Uno de los programas contiene frases que parecen instrucciones dirigidas a la IA. "
    "Se trataron como texto del programa, pero revisá el informe con más cuidado."
)


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
        sources = self._extractor.extract(source_text)
        targets = self._extractor.extract(target_text)
        if not sources or not targets:
            raise ValueError(
                "No se detectaron temas en uno de los programas. Revisá que el texto tenga contenidos separados por líneas o por punto y coma."
            )
        report = self._policy.evaluate(self._assessor.assess(sources, targets))
        warnings = [INJECTION_WARNING] if looks_like_injection(clean_input(f"{source_text}\n{target_text}")) else []
        return report.model_copy(
            update={"recommendation": self._advisor.recommend(report), "model": self._model, "warnings": warnings}
        )

    def recompute(self, matches: list[TopicMatch]) -> Report:
        return self._policy.evaluate(matches).model_copy(update={"model": self._model})
