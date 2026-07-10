from __future__ import annotations

from repair.models import FailureFamily, RepairSlice, Slice, RepairCard, RepairParam

# Template: (label, pipeline_stage, params, expected_benefit, expected_tradeoff, repair_type, confidence_base)
_TEMPLATES: dict[RepairSlice, tuple] = {
    RepairSlice.R1_partial_coverage: (
        "Widen retrieval to improve evidence coverage",
        "retriever / chunking",
        [
            {"name": "retriever_top_k", "current_value": 3, "suggested_value": 6,
             "description": "Return more candidates to improve coverage."},
            {"name": "chunk_overlap", "current_value": 20, "suggested_value": 50,
             "description": "Wider overlap preserves cross-boundary evidence."},
            {"name": "reranker_enabled", "current_value": False, "suggested_value": True,
             "description": "Reranker promotes the most relevant chunks to the top."},
        ],
        "Better coverage of relevant aspects.",
        "More latency and context volume.",
        "executable", 0.80,
    ),
    RepairSlice.R2_noisy_retrieval: (
        "Reduce retrieval noise with reranker and smaller chunks",
        "retriever / reranker / chunking",
        [
            {"name": "reranker_enabled", "current_value": False, "suggested_value": True,
             "description": "Filter out weak chunks after initial retrieval."},
            {"name": "chunk_size", "current_value": 100, "suggested_value": 250,
             "description": "Smaller chunks improve precision."},
        ],
        "Cleaner evidence set with fewer distractors.",
        "Possible lower recall on edge cases.",
        "executable", 0.75,
    ),
    RepairSlice.R3_evidence_ignored: (
        "Force evidence use with grounded prompt mode",
        "generator / prompt",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "grounded",
             "description": "Require model to ground answer in retrieved context."},
        ],
        "Better context utilization and faithfulness.",
        "Answers may become shorter or more conservative.",
        "executable", 0.75,
    ),
    RepairSlice.R4_fragmented_evidence: (
        "Reduce chunk fragmentation with wider overlap",
        "chunking / retriever",
        [
            {"name": "chunk_overlap", "current_value": 20, "suggested_value": 80,
             "description": "Wider overlap keeps cross-boundary content together."},
            {"name": "chunk_size", "current_value": 100, "suggested_value": 500,
             "description": "Slightly larger chunks capture full sentences."},
            {"name": "retriever_top_k", "current_value": 3, "suggested_value": 5,
             "description": "More candidates compensates for fragmentation."},
        ],
        "Evidence no longer split across chunk boundaries.",
        "More context duplication; possible latency increase.",
        "executable", 0.70,
    ),
    RepairSlice.R5_multipart_under_retrieval: (
        "Increase retrieval breadth for multi-part questions",
        "retriever",
        [
            {"name": "retriever_top_k", "current_value": 3, "suggested_value": 7,
             "description": "More candidates covers all sub-question aspects."},
            {"name": "reranker_enabled", "current_value": False, "suggested_value": True,
             "description": "Reranker keeps the most relevant chunks per sub-question."},
        ],
        "More retrieved context covering each sub-question.",
        "Higher latency; more context for generator to process.",
        "executable", 0.70,
    ),
    RepairSlice.R6_distractor_dominated: (
        "Enable reranker to filter distractor chunks",
        "retriever / reranker",
        [
            {"name": "reranker_enabled", "current_value": False, "suggested_value": True,
             "description": "Reranker removes off-topic chunks from the evidence set."},
            {"name": "chunk_size", "current_value": 100, "suggested_value": 300,
             "description": "Smaller chunks reduce topic mixing."},
        ],
        "Fewer distractors; answer stays on target.",
        "Risk of dropping edge-case evidence.",
        "executable", 0.70,
    ),
    RepairSlice.R7_sparse_evidence: (
        "Expand retrieval set size",
        "retriever",
        [
            {"name": "retriever_top_k", "current_value": 3, "suggested_value": 8,
             "description": "Retrieve more candidates to increase evidence volume."},
        ],
        "More context volume for the generator.",
        "Possible noise increase.",
        "executable", 0.65,
    ),
    RepairSlice.G1_temporal_misattribution: (
        "Ground temporal claims and enable abstention for date gaps",
        "generator / prompt",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "grounded",
             "description": "Do not infer dates not supported in context."},
            {"name": "abstain_if_unsupported", "current_value": False, "suggested_value": True,
             "description": "Abstain when temporal evidence is missing."},
            {"name": "temperature", "current_value": 0.3, "suggested_value": 0.1,
             "description": "Lower temperature reduces temporal hallucination."},
        ],
        "Fewer temporal hallucinations.",
        "Slight completeness drop; more conservative answers.",
        "executable", 0.80,
    ),
    RepairSlice.G2_entity_substitution: (
        "Enforce citation-only mode for entity-sensitive answers",
        "generator / prompt",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "citation_only",
             "description": "Require model to cite the source chunk for each entity claim."},
            {"name": "temperature", "current_value": 0.3, "suggested_value": 0.1,
             "description": "Reduce generation variance."},
        ],
        "Correct entity attribution.",
        "More conservative, possibly more verbose answers.",
        "executable", 0.75,
    ),
    RepairSlice.G3_unsupported_causal_bridge: (
        "Block unsupported causal inference",
        "generator / reasoning prompt",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "grounded",
             "description": "Add explicit rule: avoid unsupported causal explanations."},
        ],
        "Safer answers without invented causal chains.",
        "Less explanatory answers.",
        "executable", 0.70,
    ),
    RepairSlice.G4_omitted_qualifier: (
        "Require qualified claims with citation",
        "generator / prompt",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "grounded",
             "description": "Require explicit qualifier preservation and supporting phrase citation."},
        ],
        "More nuanced answers that preserve scope.",
        "Slightly less concise.",
        "executable", 0.65,
    ),
    RepairSlice.G5_broken_multihop: (
        "Structured evidence-anchored reasoning for multi-hop",
        "generator / reasoning",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "multi_step",
             "description": "Force step-by-step reasoning grounded in each evidence chunk."},
            {"name": "retriever_top_k", "current_value": 3, "suggested_value": 5,
             "description": "More chunks to cover each hop."},
        ],
        "Multi-hop chain correctly grounded at each step.",
        "Slower or longer answers.",
        "executable", 0.70,
    ),
    RepairSlice.G6_unsupported_synthesis: (
        "Restrict open-ended synthesis beyond evidence",
        "generator",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "grounded",
             "description": "Strict instruction to avoid unsupported synthesis."},
            {"name": "temperature", "current_value": 0.3, "suggested_value": 0.1,
             "description": "Reduce inferential generation."},
        ],
        "Safer, evidence-bounded answers.",
        "Less rich synthesis answers.",
        "executable", 0.65,
    ),
    RepairSlice.G7_citation_drift: (
        "Anchor answer to specific supporting chunk",
        "generator / evidence selection",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "citation_only",
             "description": "Require model to cite and quote the specific chunk used."},
        ],
        "Higher precision; answer anchored to correct evidence.",
        "Less fluent synthesis.",
        "executable", 0.65,
    ),
    RepairSlice.S1_partial_aspect_coverage: (
        "Structured prompt to cover all question aspects",
        "generator",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "multi_step",
             "description": "Answer each sub-question explicitly."},
            {"name": "retriever_top_k", "current_value": 3, "suggested_value": 5,
             "description": "More context to cover all aspects."},
        ],
        "All aspects of the question addressed.",
        "Longer answers.",
        "executable", 0.70,
    ),
    RepairSlice.S2_shallow_summarization: (
        "Use structured answer format for richer responses",
        "generator",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "structured_output",
             "description": "Enforce a structured answer format covering all key details."},
        ],
        "More complete and specific answers.",
        "Less concise.",
        "executable", 0.65,
    ),
    RepairSlice.S3_underused_evidence: (
        "Evidence enumeration before answering",
        "generator",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "grounded",
             "description": "Enumerate all relevant chunks before drafting the answer."},
        ],
        "Better utilization of retrieved evidence.",
        "More verbose answers.",
        "executable", 0.65,
    ),
    RepairSlice.A1_confident_unsupported: (
        "Enable abstention for unanswerable questions",
        "policy / generator",
        [
            {"name": "abstain_if_unsupported", "current_value": False, "suggested_value": True,
             "description": "Model should say 'I don't know' when context lacks the answer."},
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "abstain_aware",
             "description": "Add abstention examples to the prompt."},
        ],
        "Fewer confident wrong answers.",
        "More refusals; may frustrate users on borderline cases.",
        "executable", 0.85,
    ),
    RepairSlice.A2_partial_evidence_overconfidence: (
        "Constrain answers to supported evidence only",
        "generator / policy",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "grounded",
             "description": "Do not extrapolate beyond what context supports."},
            {"name": "abstain_if_unsupported", "current_value": False, "suggested_value": True,
             "description": "Abstain when context is insufficient."},
        ],
        "More conservative, accurate answers.",
        "More conservative answers.",
        "executable", 0.75,
    ),
    RepairSlice.A3_ambiguous_forced_answer: (
        "Switch to refusal/clarification mode for ambiguous questions",
        "policy",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "abstain_aware",
             "description": "Prompt model to ask for clarification or decline on ambiguous inputs."},
        ],
        "Fewer overconfident answers on ambiguous questions.",
        "More 'I don't know' answers.",
        "executable", 0.65,
    ),
    RepairSlice.Q1_rambling: (
        "Lower temperature and use concise prompt",
        "generator",
        [
            {"name": "temperature", "current_value": 0.3, "suggested_value": 0.1,
             "description": "Reduce generation variance and filler."},
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "structured_output",
             "description": "Enforce concise structured output."},
        ],
        "More focused, concise answers.",
        "Less expressive answers.",
        "executable", 0.70,
    ),
    RepairSlice.Q2_poor_structure: (
        "Use structured output template",
        "generator",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "structured_output",
             "description": "Enforce a clear, structured answer format."},
        ],
        "Better readability and flow.",
        "Less flexible output style.",
        "executable", 0.65,
    ),
    RepairSlice.Q3_internal_inconsistency: (
        "Structured reasoning prompt to prevent contradictions",
        "generator",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "multi_step",
             "description": "Force step-by-step reasoning to maintain internal consistency."},
            {"name": "temperature", "current_value": 0.3, "suggested_value": 0.0,
             "description": "Deterministic generation reduces drift."},
        ],
        "Internally consistent answers.",
        "More rigid output.",
        "executable", 0.65,
    ),
}

# Compound repair templates keyed by co-firing family pair ("retrieval+grounding", etc.)
_COMPOUND_TEMPLATES: dict[str, tuple] = {
    "retrieval+grounding": (
        "Compound repair: improve retrieval quality and constrain generation faithfulness",
        "retriever / reranker / chunking / generator / prompt",
        [
            {"name": "reranker_enabled", "current_value": False, "suggested_value": True,
             "description": "Filter weak chunks — reduces noise that leads to hallucination."},
            {"name": "retriever_top_k", "current_value": 3, "suggested_value": 5,
             "description": "More candidates improves evidence coverage."},
            {"name": "chunk_size", "current_value": 100, "suggested_value": 250,
             "description": "Smaller chunks reduce topic mixing that causes noisy retrieval."},
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "grounded",
             "description": "Ground generation strictly in retrieved evidence."},
            {"name": "temperature", "current_value": 0.3, "suggested_value": 0.1,
             "description": "Lower temperature reduces hallucination tendency."},
        ],
        "Cleaner evidence set reduces hallucination and improves faithfulness.",
        "Higher latency; more conservative answers; re-chunking required.",
        "executable", 0.70,
    ),
    "retrieval+generation": (
        "Compound repair: widen retrieval breadth and improve answer assembly",
        "retriever / reranker / chunking / generator / prompt",
        [
            {"name": "retriever_top_k", "current_value": 3, "suggested_value": 7,
             "description": "Retrieve more candidates to cover all question aspects."},
            {"name": "reranker_enabled", "current_value": False, "suggested_value": True,
             "description": "Reranker keeps the best candidates per aspect."},
            {"name": "chunk_size", "current_value": 100, "suggested_value": 250,
             "description": "Smaller chunks reduce noise and improve retrieval precision."},
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "structured_output",
             "description": "Structured prompt improves completeness, clarity and coherence."},
            {"name": "temperature", "current_value": 0.3, "suggested_value": 0.1,
             "description": "Lower temperature improves answer consistency and reduces rambling."},
        ],
        "Better coverage of question aspects with cleaner, well-structured answers.",
        "Longer answers; higher latency; re-chunking required.",
        "executable", 0.65,
    ),
    "grounding+generation": (
        "Compound repair: anchor generation and improve output structure",
        "generator / prompt",
        [
            {"name": "prompt_mode", "current_value": "normal", "suggested_value": "citation_only",
             "description": "Citation-only mode reduces hallucination and forces structured evidence use."},
            {"name": "retriever_top_k", "current_value": 3, "suggested_value": 5,
             "description": "More context for the generator to draw complete, grounded answers."},
            {"name": "temperature", "current_value": 0.3, "suggested_value": 0.1,
             "description": "Lower temperature reduces both hallucination and verbosity."},
        ],
        "Fewer hallucinations and more coherent, complete answers.",
        "More conservative; less fluent synthesis.",
        "executable", 0.60,
    ),
}


def _detect_compound(sl: Slice) -> str | None:
    """Detect a co-firing compound pattern from secondary family signals."""
    # Primary family name is known; look for secondary family in matched signals
    if not sl.cases:
        return None
    primary = sl.family.value
    for sc in sl.cases:
        sec = sc.secondary_family
        if sec is not None and sec.value != "none":
            pair = f"{primary}+{sec.value}"
            if pair in _COMPOUND_TEMPLATES:
                return pair
            pair_rev = f"{sec.value}+{primary}"
            if pair_rev in _COMPOUND_TEMPLATES:
                return pair_rev
    return None


def build_repair_card(sl: Slice) -> RepairCard | None:
    # Detect compound failure and use a compound template when available
    compound = _detect_compound(sl)
    if compound:
        label, pipeline_stage, param_dicts, benefit, tradeoff, repair_type, base_conf = _COMPOUND_TEMPLATES[compound]
        params = [RepairParam(**p) for p in param_dicts]
        affected = [sc.case.case_id for sc in sl.cases]
        confidence = round(base_conf * min(1.0, sl.size / 5), 3)
        rationale = (
            f"Compound failure detected: {compound.replace('+', ' + ')} signals co-fire. "
            f"A single-family repair would address only part of the problem. "
            f"This card patches both layers simultaneously."
        )
        return RepairCard(
            card_id=f"{sl.slice_type.value[:16]}_c",
            slice_type=sl.slice_type,
            slice_label=sl.slice_label,
            family=sl.family,
            pipeline_stage=pipeline_stage,
            label=label,
            rationale=rationale,
            params=params,
            expected_benefit=benefit,
            expected_tradeoff=tradeoff,
            suggested_scope="current slice",
            repair_type=repair_type,
            confidence=confidence,
            affected_cases=affected,
        )

    template = _TEMPLATES.get(sl.slice_type)
    if template is None:
        return None

    label, pipeline_stage, param_dicts, benefit, tradeoff, repair_type, base_conf = template
    params = [RepairParam(**p) for p in param_dicts]
    affected = [sc.case.case_id for sc in sl.cases]
    confidence = round(base_conf * min(1.0, sl.size / 5), 3)

    # Deterministic ID so Streamlit button keys stay stable across reruns
    card_id = sl.slice_type.value[:16]

    return RepairCard(
        card_id=card_id,
        slice_type=sl.slice_type,
        slice_label=sl.slice_label,
        family=sl.family,
        pipeline_stage=pipeline_stage,
        label=label,
        params=params,
        expected_benefit=benefit,
        expected_tradeoff=tradeoff,
        suggested_scope="current slice",
        repair_type=repair_type,
        confidence=confidence,
        affected_cases=affected,
    )
