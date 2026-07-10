from __future__ import annotations

import json
from pathlib import Path

from repair.models import (
    AspectCoverage,
    ChunkRelevance,
    DiagnosticFields,
    EvalCase,
    HallucinatedClaim,
    RAGVueScores,
)


def _extract_diagnostics(details: dict) -> DiagnosticFields:
    # Hallucinated claims
    faith = details.get("strict_faithfulness", {})
    raw_hall = faith.get("hallucinated_claims", [])
    hallucinated = [
        HallucinatedClaim(
            claim=h.get("claim", ""),
            type=h.get("type", ""),
            reason=h.get("reason", ""),
        )
        for h in raw_hall
    ]
    supported = faith.get("supported_claims", [])

    # Chunk utilization
    util = details.get("context_utilization", {})
    utilized = util.get("utilized_chunks", [])
    unused = util.get("unused_chunks", [])

    # Per-chunk relevance
    ret = details.get("retrieval_relevance", {})
    per_chunk = [
        ChunkRelevance(
            chunk_id=c.get("chunk_id", i),
            relevance=c.get("relevance", 0.0),
            reason=c.get("reason", ""),
        )
        for i, c in enumerate(ret.get("per_chunk", []))
    ]

    # Aspect coverage
    comp = details.get("answer_completeness", {})
    per_aspect = [
        AspectCoverage(aspect=a.get("aspect", ""), covered=a.get("covered", False))
        for a in comp.get("per_aspect", [])
    ]
    missing_aspects = [a.aspect for a in per_aspect if not a.covered]

    # Coherence
    coh = details.get("coherence", {})
    contradictions = [str(c) for c in coh.get("contradictions", [])]
    logical_issues = [str(i) for i in coh.get("logical_issues", [])]

    # Clarity
    clar = details.get("clarity", {})
    clarity_issues = [str(i) for i in clar.get("issues", [])]

    # Answer relevance
    rel = details.get("answer_relevance", {})
    missing_parts = [str(p) for p in rel.get("missing_parts", [])]

    return DiagnosticFields(
        hallucinated_claims=hallucinated,
        supported_claims=supported,
        utilized_chunks=utilized,
        unused_chunks=unused,
        per_chunk_relevance=per_chunk,
        per_aspect=per_aspect,
        missing_aspects=missing_aspects,
        contradictions=contradictions,
        logical_issues=logical_issues,
        clarity_issues=clarity_issues,
        missing_parts=missing_parts,
    )


def _derive_proxy_metrics(
    scores: RAGVueScores,
    diag: DiagnosticFields,
    is_answerable: bool | None,
    answer: str,
) -> RAGVueScores:
    """
    Derive optional RAGVue metrics that our current judge doesn't produce,
    using available scores and diagnostic fields as proxies.
    """
    # retrieval_coverage: fraction of question aspects covered by retrieved evidence
    if scores.retrieval_coverage is None:
        if diag.per_aspect:
            covered = sum(1 for a in diag.per_aspect if a.covered)
            scores.retrieval_coverage = round(covered / len(diag.per_aspect), 3)
        else:
            scores.retrieval_coverage = scores.retrieval_relevance

    # multi_hop_faithfulness: degraded if broken hops detected, else use faithfulness
    if scores.multi_hop_faithfulness is None:
        if diag.broken_hops:
            scores.multi_hop_faithfulness = 0.0
        else:
            scores.multi_hop_faithfulness = scores.strict_faithfulness

    # implicit_contradiction: penalise for each detected contradiction
    if scores.implicit_contradiction is None:
        n = len(diag.contradictions)
        scores.implicit_contradiction = max(0.0, round(1.0 - 0.25 * n, 3))

    # calibration_stability: average of coherence and clarity (both judge-assigned)
    if scores.calibration_stability is None:
        scores.calibration_stability = round((scores.coherence + scores.clarity) / 2, 3)

    # answer_conciseness: penalise very long answers (proxy for rambling)
    if scores.answer_conciseness is None:
        word_count = len(answer.split())
        if word_count > 120:
            scores.answer_conciseness = max(0.3, round(1.0 - (word_count - 120) / 300, 3))
        else:
            scores.answer_conciseness = 1.0

    # negative_rejection: did the model answer when it should have abstained?
    if scores.negative_rejection is None:
        if is_answerable is False and scores.answer_relevance > 0.5:
            # Unanswerable question but model gave a confident answer
            scores.negative_rejection = 0.0
        elif scores.context_utilization < 0.15 and scores.answer_relevance > 0.65:
            # Model answered confidently with almost no context used
            scores.negative_rejection = 0.2
        else:
            scores.negative_rejection = 1.0

    return scores


def load_eval_results(path: Path) -> list[EvalCase]:
    data = json.loads(path.read_text())
    results = data.get("results", data) if isinstance(data, dict) else data

    cases: list[EvalCase] = []
    for i, r in enumerate(results):
        scores = RAGVueScores.from_dict(r.get("ragvue_scores", {}))
        diagnostics = _extract_diagnostics(r.get("ragvue_details", {}))
        is_answerable = r.get("is_answerable")
        answer = r.get("answer", "")
        scores = _derive_proxy_metrics(scores, diagnostics, is_answerable, answer)
        case_id = (
            r.get("case_id")
            or f"{r.get('question_id', 'q')}_{r.get('retriever', str(i))}"
        )
        cases.append(EvalCase(
            case_id=case_id,
            question=r.get("question", ""),
            question_type=r.get("question_type", ""),
            retriever=r.get("retriever", ""),
            answer=answer,
            contexts=r.get("contexts") or r.get("retrieved_contexts", []),
            expected_answer=r.get("expected") or r.get("expected_answer") or "",
            is_answerable=is_answerable,
            scores=scores,
            diagnostics=diagnostics,
            metadata=r.get("metadata", {}),
        ))
    return cases


def load_ragas_results(data) -> list[EvalCase]:
    """
    Load RAGAS evaluation output into Rectify EvalCase records.

    Accepts ragas.EvaluationResult, pandas DataFrame, list of dicts,
    or a path to a CSV / JSON / JSONL file.

    Layer 1 (macro family routing) works fully.
    Layer 2 slice resolution is coarser — diagnostic fields are absent,
    so G-family slices default to G6 and R3/R5 default to R1/R2.
    """
    from repair.adapters import from_ragas
    return from_ragas(data)


def load_synthetic_cases(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            cases.append(EvalCase(
                case_id=r["case_id"],
                question=r["question"],
                contexts=r.get("contexts") or r.get("retrieved_contexts", []),
                answer=r.get("answer", ""),
                metadata={
                    "intended_family": r.get("intended_family"),
                    "intended_subcluster": r.get("intended_subcluster"),
                    "notes": r.get("notes"),
                },
            ))
    return cases
