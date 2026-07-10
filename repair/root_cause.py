from __future__ import annotations

from repair.models import RepairSlice, Slice

_ROOT_CAUSES: dict[RepairSlice, tuple[str, str]] = {
    RepairSlice.R1_partial_coverage: (
        "top_k too low or retrieval breadth weak — evidence set is incomplete.",
        "Increase retriever_top_k and chunk_overlap to widen the evidence net.",
    ),
    RepairSlice.R2_noisy_retrieval: (
        "Retriever precision is weak — many irrelevant chunks crowd out relevant ones.",
        "Enable reranker_enabled and consider smaller chunk_size to improve signal quality.",
    ),
    RepairSlice.R3_evidence_ignored: (
        "Generator is not evidence-anchored — relevant chunks are retrieved but unused.",
        "Switch prompt_mode to grounded or citation_only to force evidence use.",
    ),
    RepairSlice.R4_fragmented_evidence: (
        "chunk_size too small or overlap too low — evidence is split across adjacent chunks.",
        "Increase chunk_overlap and slightly increase chunk_size to preserve cross-boundary content.",
    ),
    RepairSlice.R5_multipart_under_retrieval: (
        "Retrieval pipeline does not handle composite questions — only the first sub-question is covered.",
        "Increase retriever_top_k and enable reranker; consider query decomposition later.",
    ),
    RepairSlice.R6_distractor_dominated: (
        "Retriever over-matches on lexical terms and brings in unrelated chunks.",
        "Enable reranker_enabled and tune chunk_size to reduce distractor noise.",
    ),
    RepairSlice.R7_sparse_evidence: (
        "Retrieval set is simply too small — model uses what little it found.",
        "Increase retriever_top_k significantly; review corpus coverage.",
    ),
    RepairSlice.G1_temporal_misattribution: (
        "Generator over-generalises time-sensitive claims and infers unsupported dates.",
        "Set prompt_mode=grounded and abstain_if_unsupported=true for temporal gaps.",
    ),
    RepairSlice.G2_entity_substitution: (
        "Generator confuses similar entities — swaps person, company, or place names.",
        "Use citation_only prompt mode with stronger evidence anchoring.",
    ),
    RepairSlice.G3_unsupported_causal_bridge: (
        "Model synthesises beyond evidence — invents causal connections not in the context.",
        "Set prompt_mode=grounded and add explicit rule to avoid unsupported causal inference.",
    ),
    RepairSlice.G4_omitted_qualifier: (
        "Generator compresses qualifiers away — scope shifts or negation flips go unnoticed.",
        "Set prompt_mode=grounded and require qualified claims with citation of supporting phrases.",
    ),
    RepairSlice.G5_broken_multihop: (
        "Generator composes facts incorrectly across chunks — reasoning chain is not fully grounded.",
        "Use a structured 'reason from evidence' prompt with evidence-anchored intermediate steps.",
    ),
    RepairSlice.G6_unsupported_synthesis: (
        "Prompt is too open-ended — answer style is overly inferential across multiple claims.",
        "Set prompt_mode=grounded with stricter instruction to avoid unsupported synthesis.",
    ),
    RepairSlice.G7_citation_drift: (
        "Answer is not well anchored to the specific supporting chunk — leans on the wrong evidence.",
        "Use citation_only mode with evidence sentence extraction before answering.",
    ),
    RepairSlice.S1_partial_aspect_coverage: (
        "Generator fails to answer all parts of a multi-part question.",
        "Use structured 'answer all parts' prompt or completeness-oriented mode.",
    ),
    RepairSlice.S2_shallow_summarization: (
        "Answer planning is too shallow — covers topic but misses key specifics.",
        "Use a structured answer format and increase context usage.",
    ),
    RepairSlice.S3_underused_evidence: (
        "Generator ignores some retrieved evidence even though it was relevant.",
        "Use grounded prompt with evidence enumeration before answering.",
    ),
    RepairSlice.A1_confident_unsupported: (
        "No abstention rule in place — model answers even with no supporting evidence.",
        "Set abstain_if_unsupported=true and add a refusal template to the prompt.",
    ),
    RepairSlice.A2_partial_evidence_overconfidence: (
        "Model extrapolates beyond limited context — partial evidence triggers confident answer.",
        "Set prompt_mode=grounded and abstain_if_unsupported=true.",
    ),
    RepairSlice.A3_ambiguous_forced_answer: (
        "Prompt encourages answering under ambiguity — model answers when it should clarify.",
        "Switch to refusal/clarification mode in the prompt.",
    ),
    RepairSlice.Q1_rambling: (
        "Prompt is too open-ended and temperature is high — answer contains filler.",
        "Lower temperature and use a concise/structured prompt.",
    ),
    RepairSlice.Q2_poor_structure: (
        "Prompt lacks structure guidance — answer is hard to read or poorly organised.",
        "Use a structured_output prompt template.",
    ),
    RepairSlice.Q3_internal_inconsistency: (
        "Generator drifts across the answer — contradicts itself internally.",
        "Use a structured reasoning prompt and lower temperature.",
    ),
    RepairSlice.none: ("No failure detected.", "No repair needed."),
}


def infer_root_cause(sl: Slice) -> dict[str, str]:
    hypothesis, action = _ROOT_CAUSES.get(sl.slice_type, ("Unknown failure pattern.", "Inspect manually."))
    return {"hypothesis": hypothesis, "action": action}
