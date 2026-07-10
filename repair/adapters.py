"""
RAGAS → Rectify adapter.

RAGAS produces scores but no diagnostic fields. This means:
  - Layer 1 (macro family routing) works fully — all 6 families reachable
  - Layer 2 (repair slice assignment) degrades gracefully:
      * R-family: R1/R2/R7 reachable via scores; R3/R4/R5/R6 require diagnostics → fall to R1
      * G-family: G1-G5/G7 require hallucination type diagnostics → all fall to G6 (catch-all)
      * S-family: S2/S3 reachable via scores; S1 requires per_aspect data → falls to S2
      * A/Q/I families: fully reachable via scores alone

RAGAS metric → Rectify field mapping:
  faithfulness        → strict_faithfulness
  answer_relevancy    → answer_relevance
  context_precision   → retrieval_relevance
  context_recall      → retrieval_coverage      (RAGAS >= 0.1.9)
  noise_sensitivity   → (not mapped, ignored)
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from repair.models import DiagnosticFields, EvalCase, RAGVueScores

# RAGAS column name → Rectify internal field name
_FIELD_MAP: dict[str, str] = {
    "faithfulness": "strict_faithfulness",
    "answer_relevancy": "answer_relevance",
    "context_precision": "retrieval_relevance",
    "context_recall": "retrieval_coverage",
    # Some RAGAS versions use these names
    "answer_faithfulness": "strict_faithfulness",
    "answer_relevance": "answer_relevance",
    "context_relevance": "retrieval_relevance",
}


def from_ragas(data: Any) -> list[EvalCase]:
    """
    Convert RAGAS evaluation output to a list of Rectify EvalCase records.

    Accepts:
      - ragas.EvaluationResult  (the object returned by ragas.evaluate())
      - pandas DataFrame        (result.to_pandas())
      - list of dicts           (each dict is one row)
      - Path / str              to a CSV, JSON, or JSONL file exported from RAGAS

    Returns EvalCase list ready to pass to slice_cases().
    Proxy metrics (calibration_stability, negative_rejection, etc.) are derived
    automatically from the mapped scores.
    """
    rows = _normalise_input(data)
    cases: list[EvalCase] = []

    for i, row in enumerate(rows):
        scores = _map_scores(row)
        diag = DiagnosticFields()  # RAGAS has no diagnostic fields

        case_id = (
            row.get("case_id")
            or row.get("question_id")
            or f"ragas_{i}"
        )
        contexts = _parse_contexts(row.get("contexts", []))

        cases.append(EvalCase(
            case_id=str(case_id),
            question=str(row.get("question", "")),
            answer=str(row.get("answer", "")),
            contexts=contexts,
            expected_answer=str(row.get("ground_truth", row.get("expected_answer", ""))),
            scores=scores,
            diagnostics=diag,
            metadata={"source": "ragas"},
        ))

    # Derive proxy metrics (calibration_stability, negative_rejection, etc.)
    from repair.loader import _derive_proxy_metrics
    for case in cases:
        is_answerable = case.metadata.get("is_answerable")
        case.scores = _derive_proxy_metrics(case.scores, case.diagnostics, is_answerable, case.answer)

    return cases


# ── Internal helpers ──────────────────────────────────────────────────────────

def _normalise_input(data: Any) -> list[dict]:
    """Convert any supported input format to a list of dicts."""
    # ragas.EvaluationResult or any object with .to_pandas()
    if hasattr(data, "to_pandas"):
        return data.to_pandas().to_dict(orient="records")

    # pandas DataFrame
    try:
        import pandas as pd
        if isinstance(data, pd.DataFrame):
            return data.to_dict(orient="records")
    except ImportError:
        pass

    # File path
    if isinstance(data, (str, Path)):
        p = Path(data)
        if not p.exists():
            raise FileNotFoundError(f"RAGAS file not found: {p}")
        if p.suffix == ".csv":
            try:
                import pandas as pd
                return pd.read_csv(p).to_dict(orient="records")
            except ImportError:
                raise ImportError("pandas is required to read CSV files: pip install pandas")
        if p.suffix == ".jsonl":
            return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
        if p.suffix == ".json":
            parsed = json.loads(p.read_text())
            if isinstance(parsed, list):
                return parsed
            # RAGAS sometimes wraps results: {"results": [...]}
            return parsed.get("results", [parsed])
        raise ValueError(f"Unsupported file extension: {p.suffix}. Use .csv, .json, or .jsonl")

    # Already a list of dicts
    if isinstance(data, list):
        return data

    raise TypeError(
        f"Unsupported input type: {type(data).__name__}. "
        "Pass a ragas.EvaluationResult, pandas DataFrame, list of dicts, or file path."
    )


def _map_scores(row: dict) -> RAGVueScores:
    mapped: dict[str, float] = {}

    for ragas_key, rectify_key in _FIELD_MAP.items():
        val = row.get(ragas_key)
        if val is not None:
            try:
                mapped[rectify_key] = float(val)
            except (TypeError, ValueError):
                pass

    # coherence and clarity default to 1.0 — RAGAS has no quality metrics.
    # This means Q-family will not fire unless proxy derivation downgrades them.
    mapped.setdefault("coherence", 1.0)
    mapped.setdefault("clarity", 1.0)

    # answer_completeness: RAGAS has no direct equivalent.
    # Best proxy: context_recall (how much of the ground truth is covered).
    # If not available, fall back to answer_relevancy * 0.8 (conservative).
    if "answer_completeness" not in mapped:
        if "retrieval_coverage" in mapped:
            mapped["answer_completeness"] = round(mapped["retrieval_coverage"] * 0.85, 3)
        elif "answer_relevance" in mapped:
            mapped["answer_completeness"] = round(mapped["answer_relevance"] * 0.75, 3)

    # context_utilization: RAGAS has no equivalent.
    # Proxy: if faithfulness is high, model likely used context; if low, it may not have.
    if "context_utilization" not in mapped:
        faith = mapped.get("strict_faithfulness", 0.5)
        mapped["context_utilization"] = round(min(faith + 0.1, 1.0), 3)

    valid_fields = RAGVueScores.model_fields
    return RAGVueScores(**{k: v for k, v in mapped.items() if k in valid_fields})


def _parse_contexts(raw: Any) -> list[str]:
    """Normalise contexts to list[str] — RAGAS sometimes serialises as string repr."""
    if isinstance(raw, list):
        return [str(c) for c in raw]
    if isinstance(raw, str):
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, list):
                return [str(c) for c in parsed]
        except (ValueError, SyntaxError):
            pass
        return [raw]
    return []
