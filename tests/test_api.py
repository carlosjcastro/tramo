from fastapi.testclient import TestClient

from app.api import app
from app.container import get_service
from app.matching import TopicMatcher
from app.policy import EquivalencePolicy
from app.service import EquivalenceService
from tests.fakes import KeywordEmbedder


def fake_service() -> EquivalenceService:
    matcher = TopicMatcher(KeywordEmbedder(["bucles", "arreglos", "dom"]), covered=0.9, partial=0.5)
    return EquivalenceService(matcher, EquivalencePolicy(0.5))


app.dependency_overrides[get_service] = fake_service
client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_analyze_returns_report():
    body = client.post("/api/analyze", json={"source": "Bucles. Arreglos.", "target": "Bucles. Arreglos."}).json()
    assert body["coverage"] == 1.0
    assert body["verdict"] == "equivalencia_total"


def test_rejects_empty_program():
    assert client.post("/api/analyze", json={"source": "", "target": "Bucles"}).status_code == 422


def test_rejects_programs_without_topics():
    assert client.post("/api/analyze", json={"source": "..", "target": "Bucles"}).status_code == 422


def test_serves_interface():
    assert "Tramo" in client.get("/").text
