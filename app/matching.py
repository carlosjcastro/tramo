from app.domain import Status, Topic, TopicMatch
from app.embedding import Embedder


class TopicMatcher:
    def __init__(self, embedder: Embedder, covered: float, partial: float) -> None:
        self._embedder = embedder
        self._covered = covered
        self._partial = partial

    def match(self, source: list[Topic], target: list[Topic]) -> list[TopicMatch]:
        similarity = self._vectors(target) @ self._vectors(source).T
        best = similarity.argmax(axis=1)
        return [self._build(topic, source[j], float(similarity[i, j])) for i, (topic, j) in enumerate(zip(target, best))]

    def _vectors(self, topics: list[Topic]):
        return self._embedder.embed([topic.text for topic in topics])

    def _build(self, target: Topic, source: Topic, score: float) -> TopicMatch:
        status = self._classify(score)
        return TopicMatch(target=target, source=None if status is Status.missing else source, score=round(score, 3), status=status)

    def _classify(self, score: float) -> Status:
        if score >= self._covered:
            return Status.covered
        if score >= self._partial:
            return Status.partial
        return Status.missing
