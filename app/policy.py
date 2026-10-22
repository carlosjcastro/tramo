from app.domain import Report, Status, TopicMatch, Verdict

WEIGHTS = {Status.covered: 1.0, Status.partial: 0.5, Status.missing: 0.0}


class EquivalencePolicy:
    def __init__(self, partial_rule: float) -> None:
        self._partial_rule = partial_rule

    def evaluate(self, matches: list[TopicMatch]) -> Report:
        coverage = sum(WEIGHTS[match.status] for match in matches) / len(matches)
        pending = [match.target.text for match in matches if match.status is not Status.covered]
        return Report(matches=matches, coverage=round(coverage, 3), verdict=self._verdict(coverage, pending), pending_topics=pending)

    def _verdict(self, coverage: float, pending: list[str]) -> Verdict:
        if not pending:
            return Verdict.total
        if coverage > self._partial_rule:
            return Verdict.partial
        return Verdict.insufficient
