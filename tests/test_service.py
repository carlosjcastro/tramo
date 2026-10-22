import pytest

from app.advisor import Advisor, Recommendation
from app.assessment import Assessment, AssessmentBatch, TopicAssessor
from app.domain import Status, Verdict
from app.policy import EquivalencePolicy
from app.service import EquivalenceService
from app.topics import TopicExtractor, TopicList
from tests.fakes import RoutedLLM


def build(routes):
    llm = RoutedLLM(routes)
    return EquivalenceService(TopicExtractor(llm), TopicAssessor(llm, 12), Advisor(llm), EquivalencePolicy(0.5), llm.model)


def routes():
    assessments = AssessmentBatch(
        assessments=[
            Assessment(target_number=1, status=Status.covered, source_numbers=[1], reason="Igual."),
            Assessment(target_number=2, status=Status.partial, source_numbers=[2], reason="Parte."),
        ]
    )
    return {
        TopicList: [TopicList(topics=["Bucles", "Arreglos"]), TopicList(topics=["Bucles y ciclos", "Arreglos y objetos"])],
        AssessmentBatch: [assessments],
        Recommendation: [Recommendation(recommendation="Revisar objetos.")],
    }


def test_runs_the_whole_pipeline_and_applies_the_rule_in_code():
    report = build(routes()).analyze("origen", "destino")
    assert report.coverage == 0.75 and report.verdict is Verdict.partial
    assert report.pending_topics == ["Arreglos y objetos"]
    assert report.recommendation == "Revisar objetos." and report.model == "fake:model"


def test_recompute_applies_the_teacher_changes_without_calling_the_model():
    service = build(routes())
    matches = service.analyze("origen", "destino").matches
    matches[1] = matches[1].model_copy(update={"status": Status.covered, "overridden": True})
    report = service.recompute(matches)
    assert report.verdict is Verdict.total and report.recommendation is None


def test_fails_clearly_when_a_program_has_no_topics():
    service = build({TopicList: [TopicList(topics=["Bucles"]), TopicList(topics=["x"])]})
    with pytest.raises(ValueError):
        service.analyze("origen", "..")
