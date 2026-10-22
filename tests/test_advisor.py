from app.advisor import Advisor, Recommendation, allowed_numbers, build_prompt, keep_verified_sentences, missing_runs
from app.domain import Status, Topic, TopicMatch, Verdict
from app.policy import EquivalencePolicy
from tests.fakes import RoutedLLM


def report():
    matches = [
        TopicMatch(target=Topic(index=0, text="Bucles"), status=Status.covered, reason="Igual."),
        TopicMatch(target=Topic(index=1, text="DOM"), status=Status.missing, reason="No aparece."),
    ]
    return EquivalencePolicy(0.5).evaluate(matches)


def test_prompt_states_the_calculated_facts_and_only_the_open_topics():
    prompt = build_prompt(report())
    assert "Cobertura calculada: 50%" in prompt
    assert "evidencia insuficiente" in prompt
    assert "1. sin evidencia: DOM. No aparece." in prompt
    assert "Bucles" not in prompt


def test_returns_the_trimmed_recommendation():
    advisor = Advisor(RoutedLLM({Recommendation: [Recommendation(recommendation="  Revisar DOM primero.  ")]}))
    assert advisor.recommend(report()) == "Revisar DOM primero."
    assert report().verdict is Verdict.insufficient


def test_drops_sentences_with_numbers_the_code_did_not_calculate():
    advisor = Advisor(RoutedLLM({Recommendation: [Recommendation(recommendation="La cobertura es 50%. Faltan 18 temas web. Revisar DOM primero.")]}))
    assert advisor.recommend(report()) == "La cobertura es 50%. Revisar DOM primero."


def test_returns_nothing_when_every_sentence_has_an_unverified_number():
    assert keep_verified_sentences("Faltan 18 temas.", {50}) is None


def long_report():
    states = [Status.covered, Status.missing, Status.missing, Status.covered] + [Status.missing] * 5 + [Status.partial]
    matches = [TopicMatch(target=Topic(index=i, text=f"Tema {i}"), status=state, reason="x") for i, state in enumerate(states)]
    return EquivalencePolicy(0.5).evaluate(matches)


def test_finds_the_longest_consecutive_runs_without_evidence():
    assert missing_runs(long_report().matches) == [("Tema 4", "Tema 8", 5)]


def test_prompt_lists_the_runs_and_their_lengths_are_allowed_numbers():
    prompt = build_prompt(long_report())
    assert "Desde «Tema 4» hasta «Tema 8» (5 temas)" in prompt
    assert 5 in allowed_numbers(long_report())


def test_short_runs_are_not_reported():
    assert missing_runs(report().matches) == []
    assert "Tramos consecutivos" not in build_prompt(report())
