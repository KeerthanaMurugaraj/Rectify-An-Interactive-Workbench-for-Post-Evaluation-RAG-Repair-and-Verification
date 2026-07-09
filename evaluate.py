"""
Evaluate RAG run outputs with RAGVue, using Ollama/Mistral as the judge.

Usage:
    python evaluate.py --run runs/run_bm25.jsonl
    python evaluate.py --run runs/sample_10_results.json
    python evaluate.py  # evaluates all runs/*.jsonl
"""
import argparse
import json
import os
from pathlib import Path

# Route RAGVue to Ollama (use OLLAMA_HOST env var for Docker; defaults to localhost)
_ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
os.environ.setdefault("OPENAI_API_KEY", "ollama")
os.environ.setdefault("OPENAI_BASE_URL", f"{_ollama_host}/v1")

import ragvue.src.core.llm_judge as _lj
_lj.default_model = lambda: "mistral:latest"

import ragvue

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

EVAL_DIR = Path("evals")


def load_run(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(path.read_text())
    with open(path) as f:
        return [json.loads(line) for line in f]


def to_ragvue_item(record: dict) -> dict:
    return {
        "question": record["question"],
        "contexts": record.get("retrieved_contexts") or record.get("contexts", []),
        "answer": record["answer"],
        "expected_answer": record.get("expected_answer") or "",
        "metadata": {
            "question_id": record.get("question_id"),
            "question_type": record.get("question_type"),
            "retriever": record.get("retriever"),
            "is_answerable": record.get("is_answerable"),
        },
    }


def evaluate_run(run_path: Path) -> Path:
    records = load_run(run_path)
    print(f"\nEvaluating {run_path.name} — {len(records)} items...")
    items = [to_ragvue_item(r) for r in records]
    result = ragvue.evaluate(items, metrics=METRICS)

    # Merge scores back into records
    enriched = []
    for record, eval_item in zip(records, result["results"]):
        scores = {m["name"]: m["score"] for m in eval_item["metrics"]}
        details = {m["name"]: m.get("details", {}) for m in eval_item["metrics"]}
        enriched.append({**record, "ragvue_scores": scores, "ragvue_details": details})

    EVAL_DIR.mkdir(exist_ok=True)
    out_path = EVAL_DIR / f"eval_{run_path.stem}.json"
    out_path.write_text(json.dumps({"summary": result["summary"], "results": enriched}, indent=2))
    print(f"Saved → {out_path}")
    print("Summary:")
    for k, v in result["summary"].items():
        print(f"  {k:<30} {v:.3f}")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, default=None, help="Path to a single run file")
    args = parser.parse_args()

    if args.run:
        evaluate_run(args.run)
    else:
        runs = sorted(Path("runs").glob("*.jsonl"))
        if not runs:
            print("No .jsonl files found in runs/. Run rag/runner.py first.")
            return
        for run_path in runs:
            evaluate_run(run_path)


if __name__ == "__main__":
    main()
