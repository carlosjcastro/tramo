from app.llm import INVALID_OUTPUT, LLMError
from app.topics import TopicExtractor, TopicList
from tests.fakes import RoutedLLM


def extract(output, text="Variables y tipos. Bucles."):
    return TopicExtractor(RoutedLLM({TopicList: [output]})).extract(text)


def test_uses_the_topics_returned_by_the_model_without_duplicates():
    topics = extract(TopicList(topics=["Variables", " variables ", "Bucles", "  "]))
    assert [topic.text for topic in topics] == ["Variables", "Bucles"]
    assert [topic.index for topic in topics] == [0, 1]


def test_falls_back_to_rule_based_splitting_when_the_output_is_invalid():
    topics = extract(LLMError(INVALID_OUTPUT, "x", 502))
    assert [topic.text for topic in topics] == ["Variables y tipos", "Bucles"]


def test_does_not_hide_an_unavailable_model():
    try:
        extract(LLMError("ai_unavailable", "down", 503))
    except LLMError as error:
        assert error.code == "ai_unavailable"
    else:
        raise AssertionError("expected LLMError")


def test_rejects_an_empty_topic_list():
    try:
        extract(TopicList(topics=["", " "]))
    except ValueError:
        return
    raise AssertionError("expected ValueError")
