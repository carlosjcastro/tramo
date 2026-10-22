import pytest

from app.domain import Status, Topic, TopicMatch, Verdict
from app.policy import EquivalencePolicy


def build(statuses: list[Status]) -> list[TopicMatch]:
    return [TopicMatch(target=Topic(index=i, text=f"tema {i}"), source=None, score=0.0, status=s) for i, s in enumerate(statuses)]


@pytest.mark.parametrize(
    ("statuses", "verdict"),
    [
        ([Status.covered] * 4, Verdict.total),
        ([Status.covered, Status.covered, Status.partial, Status.missing], Verdict.partial),
        ([Status.covered, Status.missing, Status.missing, Status.missing], Verdict.insufficient),
        ([Status.covered, Status.covered, Status.missing, Status.missing], Verdict.insufficient),
    ],
)
def test_applies_the_fifty_percent_rule(statuses, verdict):
    assert EquivalencePolicy(0.5).evaluate(build(statuses)).verdict is verdict
