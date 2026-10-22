import pytest
from fastapi.testclient import TestClient

from app.advisor import Advisor, Recommendation
from app.api import app
from app.assessment import Assessment, AssessmentBatch, TopicAssessor
from app.container import get_limiters, get_llm, get_service
from app.domain import Status
from app.policy import EquivalencePolicy
from app.service import EquivalenceService
from app.topics import TopicExtractor, TopicList
from tests.documents import make_docx, make_pdf
from tests.fakes import RoutedLLM


def fake_service() -> EquivalenceService:
    llm = RoutedLLM(
        {
            TopicList: [TopicList(topics=["Bucles"]), TopicList(topics=["Bucles"])],
            AssessmentBatch: [
                AssessmentBatch(assessments=[Assessment(target_number=1, status=Status.covered, source_numbers=[1], reason="Igual.")])
            ],
            Recommendation: [Recommendation(recommendation="Todo coincide.")],
        }
    )
    return EquivalenceService(TopicExtractor(llm), TopicAssessor(llm, 12), Advisor(llm), EquivalencePolicy(0.5), llm.model)


app.dependency_overrides[get_service] = fake_service
app.dependency_overrides[get_llm] = lambda: RoutedLLM({})
client = TestClient(app, base_url="http://localhost")


@pytest.fixture(autouse=True)
def fresh_limits():
    get_limiters.cache_clear()


def upload(name: str, data: bytes):
    return client.post("/api/extract", files={"file": (name, data, "application/octet-stream")})


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_limits_report_the_model_and_whether_it_is_ready():
    body = client.get("/api/limits").json()
    assert set(body) == {"max_chars", "max_file_bytes", "model", "model_ready"}
    assert body["model"] == "fake:model" and body["model_ready"] is True


def test_analyze_returns_the_report_with_evidence_and_recommendation():
    body = client.post("/api/analyze", json={"source": "Bucles", "target": "Bucles"}).json()
    assert body["coverage"] == 1.0 and body["verdict"] == "equivalencia_total"
    assert body["matches"][0]["sources"][0]["text"] == "Bucles"
    assert body["recommendation"] == "Todo coincide." and body["model"] == "fake:model"


def test_rejects_an_empty_program():
    assert client.post("/api/analyze", json={"source": "", "target": "Bucles"}).status_code == 422


def test_recompute_returns_a_report_without_recommendation():
    match = {"target": {"index": 0, "text": "Bucles"}, "status": "parcial", "overridden": True}
    body = client.post("/api/recompute", json={"matches": [match]}).json()
    assert body["coverage"] == 0.5 and body["recommendation"] is None
    assert client.post("/api/recompute", json={"matches": []}).status_code == 422


def test_extracts_text_from_docx_and_pdf():
    assert upload("programa.docx", make_docx(["Bucles.", "Arreglos."])).json()["text"] == "Bucles.\nArreglos."
    assert "Bucles" in upload("programa.pdf", make_pdf(["Bucles."])).json()["text"]


def test_rejects_unsupported_and_corrupt_files_with_a_message():
    unsupported = upload("programa.txt", b"hola")
    assert unsupported.status_code == 415 and unsupported.json()["detail"]["code"] == "unsupported_type"
    corrupt = upload("programa.pdf", b"no es un pdf")
    assert corrupt.status_code == 422 and "dañado" in corrupt.json()["detail"]["message"]


def test_serves_the_interface():
    assert "Tramo" in client.get("/").text
