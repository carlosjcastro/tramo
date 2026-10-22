import pytest

from app.assessment import Assessment, AssessmentBatch, TopicAssessor
from app.domain import Status, Topic
from tests.fakes import RoutedLLM


def topics(*texts: str) -> list[Topic]:
    return [Topic(index=i, text=text) for i, text in enumerate(texts)]


def batch(*items: Assessment) -> AssessmentBatch:
    return AssessmentBatch(assessments=list(items))


def covered(number: int, sources: list[int], reason: str = "Coincide.") -> Assessment:
    return Assessment(target_number=number, status=Status.covered, source_numbers=sources, reason=reason)


def assess(outputs, sources, targets, size=12):
    llm = RoutedLLM({AssessmentBatch: outputs})
    return TopicAssessor(llm, size).assess(sources, targets), llm


def test_maps_numbers_back_to_topics_and_keeps_the_reason():
    matches, _ = assess(
        [batch(covered(1, [2, 1], " Mismo alcance. "), Assessment(target_number=2, status=Status.missing, source_numbers=[1], reason="No está."))],
        topics("Bucles", "Arreglos"),
        topics("Arreglos y matrices", "DOM"),
    )
    assert [source.text for source in matches[0].sources] == ["Arreglos", "Bucles"]
    assert matches[0].reason == "Mismo alcance."
    assert matches[1].status is Status.missing and matches[1].sources == []


def test_splits_the_targets_in_batches_and_always_sends_every_source():
    outputs = [batch(covered(1, [1]), covered(2, [1])), batch(covered(1, [1]))]
    matches, llm = assess(outputs, topics("Bucles"), topics("A uno", "B dos", "C tres"), size=2)
    assert len(matches) == 3 and len(llm.prompts) == 2
    assert all("1. Bucles" in prompt for prompt in llm.prompts)
    assert [match.target.text for match in matches] == ["A uno", "B dos", "C tres"]


@pytest.mark.parametrize(
    "invalid",
    [
        batch(covered(1, [1])),
        batch(covered(1, [1]), covered(1, [1])),
        batch(covered(1, [1]), covered(2, [7])),
        batch(covered(1, [1]), Assessment(target_number=2, status=Status.partial, source_numbers=[], reason="x")),
    ],
)
def test_rejects_incomplete_or_inconsistent_assessments(invalid):
    with pytest.raises(ValueError):
        assess([invalid], topics("Bucles"), topics("A uno", "B dos"))
