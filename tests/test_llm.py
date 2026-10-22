import httpx
import pytest
from ollama import ResponseError
from pydantic import BaseModel

from app.llm import INVALID_OUTPUT, LLMError, OllamaLLM
from tests.fakes import FakeChatClient


class Answer(BaseModel):
    value: int


def llm(*replies, attempts=2):
    client = FakeChatClient(*replies)
    return OllamaLLM(client, "gemma4:e4b", 8192, attempts), client


def test_sends_a_deterministic_structured_request():
    model, client = llm('{"value": 3}')
    assert model.ask("sistema", "usuario", Answer) == Answer(value=3)
    request = client.requests[0]
    assert request["options"] == {"temperature": 0, "num_ctx": 8192}
    assert request["format"]["properties"]["value"]
    assert [message["role"] for message in request["messages"]] == ["system", "user"]


def test_retries_once_when_the_output_is_invalid():
    model, client = llm("no es json", '{"value": 1}')
    assert model.ask("s", "u", Answer).value == 1
    assert len(client.requests) == 2


def test_retries_when_the_semantic_check_fails():
    def check(answer):
        if answer.value < 5:
            raise ValueError("too small")

    model, _ = llm('{"value": 1}', '{"value": 9}')
    assert model.ask("s", "u", Answer, check=check).value == 9


def test_gives_up_after_the_allowed_attempts():
    model, _ = llm("x", "y")
    with pytest.raises(LLMError) as caught:
        model.ask("s", "u", Answer)
    assert caught.value.code == INVALID_OUTPUT and caught.value.status == 502


@pytest.mark.parametrize("failure", [ConnectionError("down"), httpx.ConnectError("down")])
def test_reports_when_ollama_is_not_running(failure):
    model, _ = llm(failure)
    with pytest.raises(LLMError) as caught:
        model.ask("s", "u", Answer)
    assert caught.value.code == "ai_unavailable" and caught.value.status == 503


def test_reports_a_missing_model_with_the_pull_command():
    model, _ = llm(ResponseError("model not found", 404))
    with pytest.raises(LLMError) as caught:
        model.ask("s", "u", Answer)
    assert caught.value.code == "model_missing" and "ollama pull gemma4:e4b" in caught.value.message


@pytest.mark.parametrize(
    ("listing", "ready"),
    [(["gemma4:e4b"], True), (["otro:modelo"], False), (ConnectionError("down"), False)],
)
def test_checks_whether_the_model_is_installed(listing, ready):
    model, _ = llm(listing)
    assert model.is_ready() is ready


def test_accepts_the_implicit_latest_tag():
    client = FakeChatClient(["gemma4:latest"])
    assert OllamaLLM(client, "gemma4", 8192).is_ready() is True


def test_omits_the_think_option_by_default():
    model, client = llm('{"value": 1}')
    model.ask("s", "u", Answer)
    assert "think" not in client.requests[0]


def test_forwards_the_think_option_when_configured():
    client = FakeChatClient('{"value": 1}')
    OllamaLLM(client, "fake:model", 4096, think=False).ask("s", "u", Answer)
    assert client.requests[0]["think"] is False
