from app.domain import Status
from app.matching import TopicMatcher
from app.syllabus import split_topics
from tests.fakes import KeywordEmbedder


def test_classifies_each_target_topic():
    matcher = TopicMatcher(KeywordEmbedder(["bucles", "arreglos", "dom"]), covered=0.9, partial=0.5)
    result = matcher.match(split_topics("Bucles. Arreglos."), split_topics("Bucles. DOM."))
    assert [match.status for match in result] == [Status.covered, Status.missing]
