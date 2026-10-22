from app.domain import Report
from app.matching import TopicMatcher
from app.policy import EquivalencePolicy
from app.syllabus import split_topics


class EquivalenceService:
    def __init__(self, matcher: TopicMatcher, policy: EquivalencePolicy) -> None:
        self._matcher = matcher
        self._policy = policy

    def analyze(self, source_text: str, target_text: str) -> Report:
        source, target = split_topics(source_text), split_topics(target_text)
        if not source or not target:
            raise ValueError("Cada programa debe tener al menos un tema")
        return self._policy.evaluate(self._matcher.match(source, target))
