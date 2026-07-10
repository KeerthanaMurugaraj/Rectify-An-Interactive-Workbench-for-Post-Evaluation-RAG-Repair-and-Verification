from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class FailureFamily(str, Enum):
    retrieval = "retrieval"
    grounding = "grounding"
    generation = "generation"
    abstention = "abstention"
    none = "none"


class RepairSlice(str, Enum):
    # Retrieval
    R1_partial_coverage = "R1_partial_coverage"
    R2_noisy_retrieval = "R2_noisy_retrieval"
    R3_evidence_ignored = "R3_evidence_ignored"
    R4_fragmented_evidence = "R4_fragmented_evidence"
    R5_multipart_under_retrieval = "R5_multipart_under_retrieval"
    R6_distractor_dominated = "R6_distractor_dominated"
    R7_sparse_evidence = "R7_sparse_evidence"
    # Grounding
    G1_temporal_misattribution = "G1_temporal_misattribution"
    G2_entity_substitution = "G2_entity_substitution"
    G3_unsupported_causal_bridge = "G3_unsupported_causal_bridge"
    G4_omitted_qualifier = "G4_omitted_qualifier"
    G5_broken_multihop = "G5_broken_multihop"
    G6_unsupported_synthesis = "G6_unsupported_synthesis"
    G7_citation_drift = "G7_citation_drift"
    # Generation (synthesis + quality combined)
    S1_partial_aspect_coverage = "S1_partial_aspect_coverage"
    S2_shallow_summarization = "S2_shallow_summarization"
    S3_underused_evidence = "S3_underused_evidence"
    Q1_rambling = "Q1_rambling"
    Q2_poor_structure = "Q2_poor_structure"
    Q3_internal_inconsistency = "Q3_internal_inconsistency"
    # Abstention
    A1_confident_unsupported = "A1_confident_unsupported"
    A2_partial_evidence_overconfidence = "A2_partial_evidence_overconfidence"
    A3_ambiguous_forced_answer = "A3_ambiguous_forced_answer"
    # Fallback
    none = "none"


SLICE_TO_FAMILY: dict[RepairSlice, FailureFamily] = {
    RepairSlice.R1_partial_coverage: FailureFamily.retrieval,
    RepairSlice.R2_noisy_retrieval: FailureFamily.retrieval,
    RepairSlice.R3_evidence_ignored: FailureFamily.retrieval,
    RepairSlice.R4_fragmented_evidence: FailureFamily.retrieval,
    RepairSlice.R5_multipart_under_retrieval: FailureFamily.retrieval,
    RepairSlice.R6_distractor_dominated: FailureFamily.retrieval,
    RepairSlice.R7_sparse_evidence: FailureFamily.retrieval,
    RepairSlice.G1_temporal_misattribution: FailureFamily.grounding,
    RepairSlice.G2_entity_substitution: FailureFamily.grounding,
    RepairSlice.G3_unsupported_causal_bridge: FailureFamily.grounding,
    RepairSlice.G4_omitted_qualifier: FailureFamily.grounding,
    RepairSlice.G5_broken_multihop: FailureFamily.grounding,
    RepairSlice.G6_unsupported_synthesis: FailureFamily.grounding,
    RepairSlice.G7_citation_drift: FailureFamily.grounding,
    RepairSlice.S1_partial_aspect_coverage: FailureFamily.generation,
    RepairSlice.S2_shallow_summarization: FailureFamily.generation,
    RepairSlice.S3_underused_evidence: FailureFamily.generation,
    RepairSlice.Q1_rambling: FailureFamily.generation,
    RepairSlice.Q2_poor_structure: FailureFamily.generation,
    RepairSlice.Q3_internal_inconsistency: FailureFamily.generation,
    RepairSlice.A1_confident_unsupported: FailureFamily.abstention,
    RepairSlice.A2_partial_evidence_overconfidence: FailureFamily.abstention,
    RepairSlice.A3_ambiguous_forced_answer: FailureFamily.abstention,
    RepairSlice.none: FailureFamily.none,
}

SLICE_LABELS: dict[RepairSlice, str] = {
    RepairSlice.R1_partial_coverage: "R1. Partial coverage",
    RepairSlice.R2_noisy_retrieval: "R2. Noisy retrieval",
    RepairSlice.R3_evidence_ignored: "R3. Evidence retrieved but ignored",
    RepairSlice.R4_fragmented_evidence: "R4. Fragmented evidence",
    RepairSlice.R5_multipart_under_retrieval: "R5. Multi-part under-retrieval",
    RepairSlice.R6_distractor_dominated: "R6. Distractor-dominated retrieval",
    RepairSlice.R7_sparse_evidence: "R7. Sparse evidence set",
    RepairSlice.G1_temporal_misattribution: "G1. Temporal misattribution",
    RepairSlice.G2_entity_substitution: "G2. Entity substitution",
    RepairSlice.G3_unsupported_causal_bridge: "G3. Unsupported causal bridge",
    RepairSlice.G4_omitted_qualifier: "G4. Omitted qualifier / scope shift",
    RepairSlice.G5_broken_multihop: "G5. Broken multi-hop reasoning",
    RepairSlice.G6_unsupported_synthesis: "G6. Unsupported synthesis",
    RepairSlice.G7_citation_drift: "G7. Citation drift",
    RepairSlice.S1_partial_aspect_coverage: "S1. Partial aspect coverage",
    RepairSlice.S2_shallow_summarization: "S2. Shallow summarization",
    RepairSlice.S3_underused_evidence: "S3. Underused evidence",
    RepairSlice.Q1_rambling: "Q1. Rambling / filler-heavy",
    RepairSlice.Q2_poor_structure: "Q2. Poor structure / weak flow",
    RepairSlice.Q3_internal_inconsistency: "Q3. Internal inconsistency",
    RepairSlice.A1_confident_unsupported: "A1. Confident unsupported answer",
    RepairSlice.A2_partial_evidence_overconfidence: "A2. Partial-evidence overconfidence",
    RepairSlice.A3_ambiguous_forced_answer: "A3. Ambiguous question forced-answer",
    RepairSlice.none: "Healthy",
}


# ── Diagnostic fields extracted from ragvue_details ──────────────────────────

class HallucinatedClaim(BaseModel):
    claim: str = ""
    type: str = ""
    reason: str = ""


class ChunkRelevance(BaseModel):
    chunk_id: int = 0
    relevance: float = 0.0
    reason: str = ""


class AspectCoverage(BaseModel):
    aspect: str = ""
    covered: bool = False


class DiagnosticFields(BaseModel):
    hallucinated_claims: list[HallucinatedClaim] = Field(default_factory=list)
    supported_claims: list[dict] = Field(default_factory=list)
    utilized_chunks: list[int] = Field(default_factory=list)
    unused_chunks: list[int] = Field(default_factory=list)
    per_chunk_relevance: list[ChunkRelevance] = Field(default_factory=list)
    per_aspect: list[AspectCoverage] = Field(default_factory=list)
    missing_aspects: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    logical_issues: list[str] = Field(default_factory=list)
    clarity_issues: list[str] = Field(default_factory=list)
    missing_parts: list[str] = Field(default_factory=list)
    broken_hops: list[str] = Field(default_factory=list)
    context_sufficient: bool | None = None
    answer_refuses: bool = False

    @property
    def n_hallucinated(self) -> int:
        return len(self.hallucinated_claims)

    @property
    def n_unused_chunks(self) -> int:
        return len(self.unused_chunks)

    @property
    def hallucination_types(self) -> list[str]:
        return [h.type for h in self.hallucinated_claims]

    @property
    def has_temporal_hallucination(self) -> bool:
        temporal_keywords = ("temporal", "date", "year", "period", "time", "when")
        for h in self.hallucinated_claims:
            text = (h.type + " " + h.reason).lower()
            if any(k in text for k in temporal_keywords):
                return True
        return False

    @property
    def has_entity_hallucination(self) -> bool:
        entity_keywords = ("person", "org", "place", "entity", "name", "company", "location", "who")
        for h in self.hallucinated_claims:
            text = (h.type + " " + h.reason).lower()
            if any(k in text for k in entity_keywords):
                return True
        return False

    @property
    def has_causal_hallucination(self) -> bool:
        causal_keywords = ("causal", "cause", "because", "therefore", "result", "leads to")
        for h in self.hallucinated_claims:
            text = (h.type + " " + h.reason).lower()
            if any(k in text for k in causal_keywords):
                return True
        return False

    @property
    def n_uncovered_aspects(self) -> int:
        return sum(1 for a in self.per_aspect if not a.covered)

    @property
    def avg_chunk_relevance(self) -> float:
        if not self.per_chunk_relevance:
            return 0.0
        return sum(c.relevance for c in self.per_chunk_relevance) / len(self.per_chunk_relevance)

    @property
    def n_weak_chunks(self) -> int:
        return sum(1 for c in self.per_chunk_relevance if c.relevance < 0.5)

    @property
    def max_chunk_relevance(self) -> float:
        if not self.per_chunk_relevance:
            return 0.0
        return max(c.relevance for c in self.per_chunk_relevance)


# ── Core data models ──────────────────────────────────────────────────────────

class RAGVueScores(BaseModel):
    strict_faithfulness: float = 0.0
    answer_relevance: float = 0.0
    retrieval_relevance: float = 0.0
    answer_completeness: float = 0.0
    context_utilization: float = 0.0
    coherence: float = 1.0
    clarity: float = 1.0
    negative_rejection: float | None = None
    retrieval_coverage: float | None = None
    retrieval_overall: float | None = None
    answer_overall: float | None = None
    multi_hop_faithfulness: float | None = None
    implicit_contradiction: float | None = None
    calibration_stability: float | None = None
    answer_conciseness: float | None = None

    @classmethod
    def from_dict(cls, d: dict[str, float]) -> RAGVueScores:
        return cls(**{k: v for k, v in d.items() if k in cls.model_fields})


class EvalCase(BaseModel):
    case_id: str
    question: str
    question_type: str = ""
    retriever: str = ""
    answer: str = ""
    contexts: list[str] = Field(default_factory=list)
    expected_answer: str = ""
    is_answerable: bool | None = None
    scores: RAGVueScores = Field(default_factory=RAGVueScores)
    diagnostics: DiagnosticFields = Field(default_factory=DiagnosticFields)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SlicedCase(BaseModel):
    case: EvalCase
    family: FailureFamily
    secondary_family: FailureFamily | None = None
    slice: RepairSlice
    slice_label: str
    matched_signals: list[str] = Field(default_factory=list)


class Slice(BaseModel):
    slice_type: RepairSlice
    slice_label: str
    family: FailureFamily
    cases: list[SlicedCase] = Field(default_factory=list)
    size: int = 0
    avg_scores: dict[str, float] = Field(default_factory=dict)
    explanation: str = ""

    def model_post_init(self, __context: Any) -> None:
        self.size = len(self.cases)


class RepairParam(BaseModel):
    name: str
    current_value: Any
    suggested_value: Any
    description: str = ""


class RepairCard(BaseModel):
    card_id: str
    slice_type: RepairSlice
    slice_label: str
    family: FailureFamily
    pipeline_stage: str = ""
    label: str
    rationale: str = ""
    params: list[RepairParam] = Field(default_factory=list)
    expected_benefit: str = ""
    expected_tradeoff: str = ""
    suggested_scope: str = "current slice"
    repair_type: str = "executable"
    confidence: float = 0.0
    affected_cases: list[str] = Field(default_factory=list)
    approved: bool = False
    approved_by: str = ""
    approved_at: str = ""
