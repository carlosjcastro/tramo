from app.advisor import Advisor, Recommendation, build_prompt, keep_verified_sentences
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
