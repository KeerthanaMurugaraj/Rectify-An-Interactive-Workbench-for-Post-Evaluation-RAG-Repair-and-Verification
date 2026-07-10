from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Literal

from repair.models import EvalCase

TRACKED_METRICS = [
    "strict_faithfulness",
    "answer_relevance",
    "retrieval_relevance",
    "answer_completeness",
    "context_utilization",
    "coherence",
    "clarity",
]

CaseVerdict = Literal["improved", "unchanged", "regressed"]


@dataclass
class CaseDelta:
    case_id: str
    before: dict[str, float]
    after: dict[str, float]
    deltas: dict[str, float]
    verdict: CaseVerdict


@dataclass
class DeltaReport:
    card_id: str
    cluster_type: str
    family: str
    n_cases: int
    before_avg: dict[str, float]
    after_avg: dict[str, float]
    avg_deltas: dict[str, float]
    improved: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    regressed: list[str] = field(default_factory=list)
    case_deltas: list[CaseDelta] = field(default_factory=list)

    @property
    def improvement_rate(self) -> float:
        if self.n_cases == 0:
            return 0.0
        return round(len(self.improved) / self.n_cases, 3)

    def summary_str(self) -> str:
        lines = [
            f"Delta Report — {self.cluster_type} ({self.family})",
            f"  Cases: {self.n_cases}  improved={len(self.improved)}  unchanged={len(self.unchanged)}  regressed={len(self.regressed)}",
            f"  Improvement rate: {self.improvement_rate:.0%}",
            "  Metric deltas (avg):",
        ]
        for metric, delta in self.avg_deltas.items():
            sign = "+" if delta >= 0 else ""
            lines.append(f"    {metric:<30} {sign}{delta:+.3f}")
        return "\n".join(lines)


def _scores_dict(case: EvalCase) -> dict[str, float]:
    return {m: getattr(case.scores, m, 0.0) or 0.0 for m in TRACKED_METRICS}


def _verdict(deltas: dict[str, float]) -> CaseVerdict:
    """
    A case improved if the mean delta across key metrics is > +0.05.
    It regressed if mean delta is < -0.05. Otherwise unchanged.
    """
    key_metrics = ["strict_faithfulness", "answer_relevance", "answer_completeness"]
    vals = [deltas.get(m, 0.0) for m in key_metrics]
    avg = mean(vals)
    if avg > 0.05:
        return "improved"
    if avg < -0.05:
        return "regressed"
    return "unchanged"


def compute_delta(
    before_cases: list[EvalCase],
    after_cases: list[EvalCase],
    card_id: str,
    cluster_type: str,
    family: str,
) -> DeltaReport:
    if len(before_cases) != len(after_cases):
        raise ValueError("before and after case lists must have the same length")

    case_deltas: list[CaseDelta] = []
    for b, a in zip(before_cases, after_cases):
        b_scores = _scores_dict(b)
        a_scores = _scores_dict(a)
        deltas = {m: round(a_scores[m] - b_scores[m], 4) for m in TRACKED_METRICS}
        verdict = _verdict(deltas)
        case_deltas.append(CaseDelta(
            case_id=b.case_id,
            before=b_scores,
            after=a_scores,
            deltas=deltas,
            verdict=verdict,
        ))

    before_avg = {
        m: round(mean(cd.before[m] for cd in case_deltas), 3) for m in TRACKED_METRICS
    }
    after_avg = {
        m: round(mean(cd.after[m] for cd in case_deltas), 3) for m in TRACKED_METRICS
    }
    avg_deltas = {
        m: round(after_avg[m] - before_avg[m], 4) for m in TRACKED_METRICS
    }

    improved = [cd.case_id for cd in case_deltas if cd.verdict == "improved"]
    unchanged = [cd.case_id for cd in case_deltas if cd.verdict == "unchanged"]
    regressed = [cd.case_id for cd in case_deltas if cd.verdict == "regressed"]

    return DeltaReport(
        card_id=card_id,
        cluster_type=cluster_type,
        family=family,
        n_cases=len(case_deltas),
        before_avg=before_avg,
        after_avg=after_avg,
        avg_deltas=avg_deltas,
        improved=improved,
        unchanged=unchanged,
        regressed=regressed,
        case_deltas=case_deltas,
    )
