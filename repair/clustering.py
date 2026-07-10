from __future__ import annotations

from collections import defaultdict
from statistics import mean

from repair.models import (
    DiagnosticFields,
    EvalCase,
    FailureFamily,
    RAGVueScores,
    RepairSlice,
    Slice,
    SlicedCase,
    SLICE_LABELS,
    SLICE_TO_FAMILY,
)

# ── Layer 1: Macro family routing ─────────────────────────────────────────────

def assign_family(
    scores: RAGVueScores, diag: DiagnosticFields
) -> tuple[FailureFamily, FailureFamily | None, list[str]]:
    signals: list[str] = []

    # Evaluate each family independently so we can detect compound failures
    is_abstention = scores.negative_rejection is not None and scores.negative_rejection < 0.5
    # A retrieval failure requires that the best chunk is also weak — if at least one
    # chunk scored ≥ 0.7, the relevant evidence WAS retrieved and the failure is
    # downstream (generation ignoring the evidence), not retrieval.
    has_good_chunk = diag.max_chunk_relevance >= 0.7
    # Exception: for multi-hop / comparison questions, a single good chunk is not
    # enough — you need docs for ALL entities/hops. If retrieval_coverage < 0.7
    # despite a good chunk, the retriever missed some required documents.
    coverage = scores.retrieval_coverage or 1.0
    incomplete_coverage = has_good_chunk and coverage < 0.7 and (scores.context_utilization or 0.0) < 0.2
    is_retrieval = (
        incomplete_coverage
        or (
            not has_good_chunk
            and (
                scores.retrieval_relevance < 0.45
                or coverage < 0.45
            )
        )
    )
    # Grounding = model made claims that contradict the context (hallucination).
    # If a good chunk was retrieved but context_utilization is near zero, low
    # faithfulness means the model didn't attempt an answer — that's underused
    # evidence (generation), not hallucination (grounding).
    ctx_util = scores.context_utilization or 0.0
    is_grounding = (
        scores.strict_faithfulness < 0.5
        and not (has_good_chunk and ctx_util < 0.2)
    )
    is_generation = (
        scores.clarity < 0.5 or scores.coherence < 0.5
        or (scores.answer_completeness < 0.4 and scores.retrieval_relevance >= 0.45)
        or (has_good_chunk and not incomplete_coverage and scores.context_utilization < 0.35)  # good chunk present but model ignored it
    )

    # Primary family: priority order
    if is_abstention:
        primary = FailureFamily.abstention
        signals.append("negative_rejection < 0.5")
    elif is_retrieval:
        primary = FailureFamily.retrieval
        if incomplete_coverage:
            signals.append(f"incomplete_coverage: max_chunk={diag.max_chunk_relevance:.2f} ≥ 0.7 but retrieval_coverage={coverage:.2f} < 0.7 — retrieved some but not all required docs")
        else:
            signals.append(f"retrieval_relevance={scores.retrieval_relevance:.2f} < 0.45")
    elif is_grounding:
        primary = FailureFamily.grounding
        signals.append(f"strict_faithfulness={scores.strict_faithfulness:.2f} < 0.5")
    elif is_generation:
        primary = FailureFamily.generation
        signals.append(f"clarity={scores.clarity:.2f} / coherence={scores.coherence:.2f} / completeness={scores.answer_completeness:.2f}")
    else:
        return FailureFamily.none, None, []

    # Secondary family: first other signal that fires (excluding primary)
    secondary_candidates: list[tuple[FailureFamily, str]] = []
    if primary != FailureFamily.retrieval and is_retrieval:
        secondary_candidates.append((FailureFamily.retrieval, f"retrieval_relevance={scores.retrieval_relevance:.2f} also low"))
    if primary != FailureFamily.grounding and is_grounding:
        secondary_candidates.append((FailureFamily.grounding, f"strict_faithfulness={scores.strict_faithfulness:.2f} also low"))
    if primary != FailureFamily.generation and is_generation:
        secondary_candidates.append((FailureFamily.generation, "generation signals also present"))

    secondary: FailureFamily | None = None
    if secondary_candidates:
        secondary, sec_signal = secondary_candidates[0]
        signals.append(f"[secondary] {sec_signal}")

    return primary, secondary, signals


# ── Layer 2: Repair slice assignment within family ────────────────────────────

def assign_slice(
    family: FailureFamily,
    scores: RAGVueScores,
    diag: DiagnosticFields,
) -> tuple[RepairSlice, list[str]]:
    if family == FailureFamily.retrieval:
        return _slice_retrieval(scores, diag)
    if family == FailureFamily.grounding:
        return _slice_grounding(scores, diag)
    if family == FailureFamily.generation:
        return _slice_generation(scores, diag)
    if family == FailureFamily.abstention:
        return _slice_abstention(scores, diag)
    return RepairSlice.none, []


def _slice_retrieval(scores: RAGVueScores, diag: DiagnosticFields) -> tuple[RepairSlice, list[str]]:
    # R5: good chunk retrieved but coverage incomplete → multi-hop/comparison missing one leg
    coverage = scores.retrieval_coverage or 1.0
    if diag.max_chunk_relevance >= 0.7 and coverage < 0.7 and (scores.context_utilization or 0.0) < 0.2:
        return RepairSlice.R5_multipart_under_retrieval, [
            f"max_chunk_relevance={diag.max_chunk_relevance:.2f} — partial retrieval success",
            f"retrieval_coverage={coverage:.2f} < 0.7 — missing docs for other hop/entity",
            f"context_utilization={scores.context_utilization:.2f} — model correctly declined with incomplete context",
        ]

    # R3: good relevance but context_utilization low → generation ignores evidence
    if scores.retrieval_relevance >= 0.5 and scores.context_utilization < 0.35:
        return RepairSlice.R3_evidence_ignored, [
            f"retrieval_relevance={scores.retrieval_relevance:.2f} OK",
            f"context_utilization={scores.context_utilization:.2f} low",
            f"unused_chunks={diag.n_unused_chunks}",
        ]

    # R2: relevance low + many weak chunks → noisy retrieval
    if scores.retrieval_relevance < 0.35 and diag.n_weak_chunks >= 2:
        return RepairSlice.R2_noisy_retrieval, [
            f"retrieval_relevance={scores.retrieval_relevance:.2f} low",
            f"weak_chunks={diag.n_weak_chunks}",
        ]

    # R7: coverage very low but utilization high → sparse set (model uses what little it got)
    if scores.context_utilization >= 0.8 and scores.answer_completeness < 0.3 and scores.retrieval_relevance < 0.45:
        return RepairSlice.R7_sparse_evidence, [
            f"context_utilization={scores.context_utilization:.2f} high",
            f"answer_completeness={scores.answer_completeness:.2f} very low",
        ]

    # R5: multi-aspect question, missing aspects repeat → multi-part under-retrieval
    if diag.n_uncovered_aspects >= 2 and len(diag.per_aspect) >= 3:
        return RepairSlice.R5_multipart_under_retrieval, [
            f"uncovered_aspects={diag.n_uncovered_aspects}/{len(diag.per_aspect)}",
        ]

    # R4: coverage moderate, missing aspects spread across chunks → fragmented evidence
    if diag.n_uncovered_aspects >= 1 and diag.n_weak_chunks >= 1 and scores.retrieval_relevance < 0.5:
        return RepairSlice.R4_fragmented_evidence, [
            f"uncovered_aspects={diag.n_uncovered_aspects}",
            f"weak_chunks={diag.n_weak_chunks}",
        ]

    # R6: relevance low-moderate, many chunks unused → distractor-dominated
    if scores.retrieval_relevance < 0.5 and diag.n_unused_chunks >= 1:
        return RepairSlice.R6_distractor_dominated, [
            f"retrieval_relevance={scores.retrieval_relevance:.2f}",
            f"unused_chunks={diag.n_unused_chunks}",
        ]

    # R1: default retrieval failure → partial coverage
    return RepairSlice.R1_partial_coverage, [
        f"retrieval_relevance={scores.retrieval_relevance:.2f}",
        f"answer_completeness={scores.answer_completeness:.2f}",
    ]


def _slice_grounding(scores: RAGVueScores, diag: DiagnosticFields) -> tuple[RepairSlice, list[str]]:
    # G5: broken hops explicitly populated, OR multi_hop_faithfulness meaningfully lower than
    # strict_faithfulness (ruling out the proxy case where they are set equal)
    multihop_specific = (
        scores.multi_hop_faithfulness is not None
        and scores.multi_hop_faithfulness < 0.4
        and scores.multi_hop_faithfulness < scores.strict_faithfulness - 0.1
    )
    if len(diag.broken_hops) > 0 or multihop_specific:
        return RepairSlice.G5_broken_multihop, [
            "broken_hops detected" if diag.broken_hops else f"multi_hop_faithfulness={scores.multi_hop_faithfulness:.2f} specifically low",
        ]

    # G1: temporal hallucination signal in claims
    if diag.has_temporal_hallucination:
        return RepairSlice.G1_temporal_misattribution, [
            "hallucinated claim with temporal/date signal",
        ]

    # G2: entity-type hallucination
    if diag.has_entity_hallucination:
        return RepairSlice.G2_entity_substitution, [
            "hallucinated claim with entity/person/place signal",
        ]

    # G3: causal hallucination
    if diag.has_causal_hallucination:
        return RepairSlice.G3_unsupported_causal_bridge, [
            "hallucinated claim with causal signal",
        ]

    # G4: implicit contradiction low OR qualifier-type contradiction
    if scores.implicit_contradiction is not None and scores.implicit_contradiction < 0.4:
        return RepairSlice.G4_omitted_qualifier, [
            f"implicit_contradiction={scores.implicit_contradiction:.2f}",
        ]

    # G7: citation drift — faithfulness/context weak despite apparently relevant contexts
    if scores.retrieval_relevance >= 0.5 and scores.strict_faithfulness < 0.5 \
            and scores.context_utilization < 0.5:
        return RepairSlice.G7_citation_drift, [
            f"retrieval OK but faithfulness={scores.strict_faithfulness:.2f}",
            f"context_utilization={scores.context_utilization:.2f}",
        ]

    # G6: answer relevant but hallucinations exist without concentrated type
    if scores.answer_relevance >= 0.6 and diag.n_hallucinated > 0:
        return RepairSlice.G6_unsupported_synthesis, [
            f"answer_relevance={scores.answer_relevance:.2f} high",
            f"hallucinated_claims={diag.n_hallucinated}",
        ]

    # Default grounding failure: diffuse hallucinations with no concentrated type
    return RepairSlice.G6_unsupported_synthesis, [
        f"strict_faithfulness={scores.strict_faithfulness:.2f} low, no concentrated hallucination type",
    ]


def _slice_generation(scores: RAGVueScores, diag: DiagnosticFields) -> tuple[RepairSlice, list[str]]:
    # Quality signals checked first (more directly observable)

    # Q3: coherence low → internal inconsistency
    if scores.coherence < 0.5:
        return RepairSlice.Q3_internal_inconsistency, [
            f"coherence={scores.coherence:.2f}",
            f"logical_issues={len(diag.logical_issues)}",
        ]

    # Q2: clarity low → poor structure
    if scores.clarity < 0.5:
        return RepairSlice.Q2_poor_structure, [
            f"clarity={scores.clarity:.2f}",
            f"clarity_issues={len(diag.clarity_issues)}",
        ]

    # Q1: conciseness low
    if scores.answer_conciseness is not None and scores.answer_conciseness < 0.5:
        return RepairSlice.Q1_rambling, [f"answer_conciseness={scores.answer_conciseness:.2f}"]

    # Synthesis signals

    # S3: relevant chunks retrieved but unused
    if diag.n_unused_chunks >= 1 and scores.context_utilization < 0.5:
        return RepairSlice.S3_underused_evidence, [
            f"unused_chunks={diag.n_unused_chunks}",
            f"context_utilization={scores.context_utilization:.2f}",
        ]

    # S1: multiple aspects uncovered → multi-part question
    if diag.n_uncovered_aspects >= 2:
        return RepairSlice.S1_partial_aspect_coverage, [
            f"uncovered_aspects={diag.n_uncovered_aspects}/{len(diag.per_aspect)}",
        ]

    # S2: default shallow summarization
    return RepairSlice.S2_shallow_summarization, [
        f"answer_completeness={scores.answer_completeness:.2f}",
    ]


def _slice_abstention(scores: RAGVueScores, diag: DiagnosticFields) -> tuple[RepairSlice, list[str]]:
    # A3: instability indicators alongside negative rejection → ambiguous forced-answer
    if scores.calibration_stability is not None and scores.calibration_stability < 0.5:
        return RepairSlice.A3_ambiguous_forced_answer, ["negative_rejection failure + instability"]

    # A2: some relevant evidence exists but model over-commits
    if scores.retrieval_relevance >= 0.4:
        return RepairSlice.A2_partial_evidence_overconfidence, [
            f"some retrieval relevance={scores.retrieval_relevance:.2f} but negative_rejection failure",
        ]

    # A1: confident answer with no supporting evidence
    return RepairSlice.A1_confident_unsupported, ["negative_rejection failure, low retrieval"]


# ── Gold-answer similarity pre-filter ────────────────────────────────────────

_embed_model = None

def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _embed_model = False  # mark unavailable so we don't retry
    return _embed_model if _embed_model is not False else None


def _answer_similarity(a: str, b: str) -> float:
    """Cosine similarity via all-MiniLM-L6-v2; falls back to token Jaccard if model unavailable.

    Short gold answers (≤ 5 words) that appear verbatim inside the generated answer are
    treated as a full match (1.0) — embedding similarity underestimates these because a
    full-sentence answer and a single-word gold have very different vector norms.
    """
    if not a or not b:
        return 0.0
    # Verbatim substring check for short gold answers (entity / date / name answers)
    if len(b.split()) <= 5 and b.lower().strip() in a.lower():
        return 1.0
    model = _get_embed_model()
    if model is not None:
        import numpy as np
        vecs = model.encode([a, b], normalize_embeddings=True)
        return float(np.dot(vecs[0], vecs[1]))
    # fallback: token Jaccard
    ta, tb = set(a.lower().split()), set(b.lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


GOLD_MATCH_THRESHOLD = 0.6
SHORT_ANSWER_SIM_THRESHOLD = 0.95  # bypass grounding check for ≤3-word gold answers


# ── Public API ────────────────────────────────────────────────────────────────

def slice_cases(cases: list[EvalCase]) -> list[SlicedCase]:
    result: list[SlicedCase] = []
    for case in cases:
        # Pre-filter 0: unanswerable question where model correctly abstained.
        # negative_rejection ≥ 0.5 means the model said "I don't know" — that is
        # the right behaviour; low faithfulness/utilization scores are meaningless
        # here because there is no answer to be faithful to.
        if case.is_answerable is False:
            neg_rej = case.scores.negative_rejection or 0.0
            if neg_rej >= 0.5:
                result.append(SlicedCase(
                    case=case,
                    family=FailureFamily.none,
                    secondary_family=None,
                    slice=RepairSlice.none,
                    slice_label=SLICE_LABELS[RepairSlice.none],
                    matched_signals=[f"correct_abstention: is_answerable=False and negative_rejection={neg_rej:.2f} ≥ 0.5 — model correctly declined to answer"],
                ))
                continue

        # Pre-filter 1: skip only if answer matches gold AND is grounded in context.
        # Similarity alone is insufficient — a hallucinated answer can match gold
        # by coincidence or prior knowledge without using the retrieved evidence.
        ungrounded_signal: str | None = None
        if case.expected_answer and case.answer:
            sim = _answer_similarity(case.answer, case.expected_answer)
            faith = case.scores.strict_faithfulness or 0.0
            ctx_util = case.scores.context_utilization or 0.0
            # Grounding has three acceptable conditions:
            # 1. faithfulness ≥ 0.5 — RAGVue confirms the answer is supported by context
            # 2. context_utilization ≥ 0.5 — model demonstrably used the retrieved chunks
            # 3. short-answer relaxation: gold ≤ 3 words, sim ≥ 0.95, model did not refuse
            #    RAGVue's faithfulness judge cannot reliably evaluate one-word answers
            #    (e.g. "Before", "2016", "Dublin") — it invents implied claims from context
            #    and penalises them, producing artificially low scores for correct answers.
            #    The refusal guard prevents firing when the gold word appears inside an
            #    "I don't know" explanation and fools the verbatim similarity check.
            _answer_lower = (case.answer or "").lower()
            _refuses = any(p in _answer_lower for p in [
                "i don't know", "i do not know", "cannot determine",
                "not mentioned", "not provided", "no information",
            ])
            _short_exact = (
                len((case.expected_answer or "").split()) <= 3
                and sim >= SHORT_ANSWER_SIM_THRESHOLD
                and not _refuses
            )
            is_grounded = faith >= 0.5 or ctx_util >= 0.5 or _short_exact
            if sim >= GOLD_MATCH_THRESHOLD and is_grounded:
                if faith >= 0.5:
                    grounded_by = f"faithfulness={faith:.2f} ≥ 0.5"
                elif ctx_util >= 0.5:
                    grounded_by = f"context_utilization={ctx_util:.2f} ≥ 0.5"
                else:
                    grounded_by = f"short_answer exact match sim={sim:.2f} ≥ {SHORT_ANSWER_SIM_THRESHOLD} (faithfulness check relaxed)"
                result.append(SlicedCase(
                    case=case,
                    family=FailureFamily.none,
                    secondary_family=None,
                    slice=RepairSlice.none,
                    slice_label=SLICE_LABELS[RepairSlice.none],
                    matched_signals=[f"gold_match: semantic_similarity={sim:.2f} ≥ {GOLD_MATCH_THRESHOLD}, {grounded_by} — correct and grounded, skipped"],
                ))
                continue
            if sim >= GOLD_MATCH_THRESHOLD and not is_grounded:
                ungrounded_signal = (
                    f"correct_answer_but_ungrounded: sim={sim:.2f} ≥ {GOLD_MATCH_THRESHOLD} "
                    f"but faithfulness={faith:.2f} < 0.5 and context_utilization={ctx_util:.2f} < 0.5 "
                    f"— answer likely from prior knowledge, retrieval still failing"
                )

        family, secondary_family, family_signals = assign_family(case.scores, case.diagnostics)
        slice_type, slice_signals = assign_slice(family, case.scores, case.diagnostics)
        all_signals = family_signals + slice_signals
        if ungrounded_signal:
            all_signals = [ungrounded_signal] + all_signals
        result.append(SlicedCase(
            case=case,
            family=family,
            secondary_family=secondary_family,
            slice=slice_type,
            slice_label=SLICE_LABELS[slice_type],
            matched_signals=all_signals,
        ))
    return result


def build_slices(sliced_cases: list[SlicedCase]) -> list[Slice]:
    groups: dict[RepairSlice, list[SlicedCase]] = defaultdict(list)
    for sc in sliced_cases:
        groups[sc.slice].append(sc)

    slices: list[Slice] = []
    for slice_type, members in groups.items():
        family = SLICE_TO_FAMILY[slice_type]
        avg_scores = _avg_scores(members)
        s = Slice(
            slice_type=slice_type,
            slice_label=SLICE_LABELS[slice_type],
            family=family,
            cases=members,
            avg_scores=avg_scores,
        )
        s.size = len(members)
        slices.append(s)

    slices.sort(key=lambda s: s.size, reverse=True)
    return slices


def _avg_scores(members: list[SlicedCase]) -> dict[str, float]:
    fields = [
        "strict_faithfulness", "answer_relevance", "retrieval_relevance",
        "answer_completeness", "context_utilization", "coherence", "clarity",
    ]
    return {
        f: round(mean(getattr(sc.case.scores, f) for sc in members), 3)
        for f in fields
    }
