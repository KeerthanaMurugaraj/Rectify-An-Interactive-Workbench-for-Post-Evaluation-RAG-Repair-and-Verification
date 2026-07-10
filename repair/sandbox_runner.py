from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

from repair.models import EvalCase, RAGVueScores

METRICS = [
    # Core metrics
    "strict_faithfulness",
    "answer_relevance",
    "retrieval_relevance",
    "answer_completeness",
    "context_utilization",
    "coherence",
    "clarity",
    # Extended metrics — natively supported by RAGVue
    "negative_rejection",
    "retrieval_coverage",
    "multi_hop_faithfulness",
    "implicit_contradiction",
    "answer_conciseness",
]


def _rerun_rag(cases: list[EvalCase], patched_config: dict) -> list[dict]:
    """Re-run the RAG pipeline for the given cases with a patched config."""
    from rag.chunker import load_and_chunk
    from rag.bm25_retriever import BM25Retriever
    from rag.generator import generate

    corpus_path = Path("data/corpus.jsonl")
    chunk_size = patched_config.get("chunk_size", 400)
    chunk_overlap = patched_config.get("chunk_overlap", 20)
    top_k = patched_config.get("retriever_top_k", 3)
    temperature = patched_config.get("temperature", 0.3)
    prompt_mode = patched_config.get("prompt_mode", "normal")
    abstain = patched_config.get("abstain_if_unsupported", False)
    reranker_enabled = patched_config.get("reranker_enabled", False)

    chunks = load_and_chunk(str(corpus_path), chunk_size, chunk_overlap)

    # Build the same retriever type that generated the original case
    retriever_name = cases[0].retriever if cases else "bm25"
    if retriever_name == "dense":
        from rag.dense_retriever import DenseRetriever
        retriever = DenseRetriever(chunks)
    elif retriever_name == "hybrid":
        from rag.hybrid_retriever import HybridRetriever
        retriever = HybridRetriever(chunks)
    else:
        retriever = BM25Retriever(chunks)

    # Simple reranker: retrieve more candidates then re-score by keyword overlap
    fetch_k = top_k * 3 if reranker_enabled else top_k

    results = []
    for case in cases:
        contexts = retriever.retrieve(case.question, top_k=fetch_k)
        if reranker_enabled and len(contexts) > top_k:
            contexts = _simple_rerank(case.question, contexts, top_k)
        answer = generate(
            case.question, contexts,
            temperature=temperature,
            prompt_mode=prompt_mode,
            abstain_if_unsupported=abstain,
        )
        results.append({
            "question_id": case.case_id,
            "question": case.question,
            "contexts": contexts,
            "answer": answer,
            "expected_answer": case.expected_answer,
            "config": patched_config,
        })
    return results


def _simple_rerank(question: str, contexts: list[str], top_k: int) -> list[str]:
    """Keyword overlap reranker — used when reranker_enabled=True and no cross-encoder available."""
    q_words = set(question.lower().split())
    scored = []
    for ctx in contexts:
        ctx_words = set(ctx.lower().split())
        overlap = len(q_words & ctx_words) / max(len(q_words), 1)
        scored.append((overlap, ctx))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [ctx for _, ctx in scored[:top_k]]


def _evaluate_ragvue(raw_items: list[dict]) -> list[dict]:
    _ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    os.environ.setdefault("OPENAI_API_KEY", "ollama")
    os.environ.setdefault("OPENAI_BASE_URL", f"{_ollama_host}/v1")

    import ragvue.src.core.llm_judge as _lj
    _lj.default_model = lambda: "mistral:latest"
    import ragvue

    items = [
        {
            "question": r["question"],
            "contexts": r.get("contexts", []),
            "answer": r["answer"],
            "expected_answer": r.get("expected_answer", ""),
        }
        for r in raw_items
    ]
    result = ragvue.evaluate(items, metrics=METRICS)
    if len(raw_items) != len(result["results"]):
        raise ValueError(
            f"RAGVue returned {len(result['results'])} results for {len(raw_items)} inputs"
        )
    enriched = []
    for raw, eval_item in zip(raw_items, result["results"]):
        scores = {m["name"]: m["score"] for m in eval_item["metrics"]}
        enriched.append({**raw, "ragvue_scores": scores})
    return enriched


def run_sandbox(
    cases: list[EvalCase],
    patched_config: dict,
    backend: str = "ragvue",
    custom_evaluate: Callable[[list[dict]], list[dict]] | None = None,
) -> list[EvalCase]:
    """
    Rerun and re-evaluate a subset of cases with a patched config.

    backend: "ragvue" (default) | "ragas" | "custom"
    custom_evaluate: required when backend="custom"; receives raw run dicts,
                     must return same list with "ragvue_scores" key added.
    """
    raw_items = _rerun_rag(cases, patched_config)

    if backend == "ragvue":
        evaluated = _evaluate_ragvue(raw_items)
    elif backend == "ragas":
        evaluated = _evaluate_ragas(raw_items)
    elif backend == "custom":
        if custom_evaluate is None:
            raise ValueError("custom_evaluate callable required for backend='custom'")
        evaluated = custom_evaluate(raw_items)
    else:
        raise ValueError(f"Unknown backend: {backend!r}")

    if len(cases) != len(evaluated):
        raise ValueError(
            f"Evaluation returned {len(evaluated)} results for {len(cases)} input cases"
        )
    result_cases: list[EvalCase] = []
    for orig, ev in zip(cases, evaluated):
        scores = RAGVueScores.from_dict(ev.get("ragvue_scores", {}))
        result_cases.append(orig.model_copy(update={
            "answer": ev.get("answer", orig.answer),
            "contexts": ev.get("contexts", orig.contexts),
            "scores": scores,
        }))
    return result_cases


def _evaluate_ragas(raw_items: list[dict]) -> list[dict]:
    from datasets import Dataset
    from ragas import evaluate as ragas_evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision

    dataset = Dataset.from_list([
        {
            "question": r["question"],
            "contexts": r.get("contexts", []),
            "answer": r["answer"],
            "ground_truth": r.get("expected_answer", ""),
        }
        for r in raw_items
    ])
    result = ragas_evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision])
    df = result.to_pandas()

    enriched = []
    for i, raw in enumerate(raw_items):
        row = df.iloc[i]
        scores = {
            "strict_faithfulness": float(row.get("faithfulness", 0)),
            "answer_relevance": float(row.get("answer_relevancy", 0)),
            "retrieval_relevance": float(row.get("context_precision", 0)),
        }
        enriched.append({**raw, "ragvue_scores": scores})
    return enriched
