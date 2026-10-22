import pytest

from app.advisor import Advisor, Recommendation
from app.assessment import Assessment, AssessmentBatch, TopicAssessor
from app.domain import Progress, Report, Status, Verdict
from app.llm import INVALID_OUTPUT, LLMError
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


def test_warns_when_the_topics_came_from_the_rule_based_fallback():
    fallback = routes()
    fallback[TopicList][0] = LLMError(INVALID_OUTPUT, "x", 502)
    report = build(fallback).analyze("Bucles. Arreglos.", "destino")
    assert len(report.warnings) == 1 and "método por reglas" in report.warnings[0]


def test_has_no_warning_when_the_model_extracted_the_topics():
    assert build(routes()).analyze("origen", "destino").warnings == []


def events_of(service):
    return list(service.analyze_events("origen", "destino"))


def test_emits_ordered_progress_and_ends_with_the_report():
    events = events_of(build(routes()))
    progress = [event for event in events if isinstance(event, Progress)]
    assert [event.stage for event in progress] == ["extracting_origin", "extracting_target", "assessing", "advising", "finished"]
    assert isinstance(events[-1], Report) and events[-1].coverage == 0.75


def test_progress_never_goes_backwards_and_finishes_complete():
    progress = [event for event in events_of(build(routes())) if isinstance(event, Progress)]
    ratios = [event.done / event.total for event in progress]
    assert ratios == sorted(ratios) and ratios[0] == 0 and ratios[-1] == 1


def test_reports_each_assessment_batch():
    llm = RoutedLLM(
        {
            TopicList: [TopicList(topics=["Bucles"]), TopicList(topics=["Arreglos", "Registros", "Objetos"])],
            AssessmentBatch: [
                AssessmentBatch(assessments=[Assessment(target_number=n, status=Status.missing, reason="x") for n in (1, 2)]),
                AssessmentBatch(assessments=[Assessment(target_number=1, status=Status.missing, reason="x")]),
            ],
            Recommendation: [Recommendation(recommendation="Revisar.")],
        }
    )
    service = EquivalenceService(TopicExtractor(llm), TopicAssessor(llm, 2), Advisor(llm), EquivalencePolicy(0.5), llm.model)
    batches = [(event.current, event.count) for event in service.analyze_events("o", "d") if isinstance(event, Progress) and event.stage == "assessing"]
    assert batches == [(1, 2), (2, 2)]
