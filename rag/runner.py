"""
Run all 3 baselines (bm25, dense, hybrid) over questions_100.jsonl.
Outputs: runs/run_bm25.jsonl, runs/run_dense.jsonl, runs/run_hybrid.jsonl

Usage:
    python -m rag.runner
    python -m rag.runner --retriever bm25   # single baseline
"""
import argparse
import json
import time
from pathlib import Path

from .chunker import load_and_chunk
from .bm25_retriever import BM25Retriever
from .dense_retriever import DenseRetriever
from .hybrid_retriever import HybridRetriever
from .generator import generate

CORPUS_PATH = Path("data/corpus.jsonl")
QUESTIONS_PATH = Path("data/questions_100.jsonl")
RUNS_DIR = Path("runs")

BASELINE_CONFIG = {
    "retriever_top_k": 3,
    "chunk_size": 400,
    "chunk_overlap": 20,
    "reranker_enabled": False,
    "prompt_mode": "normal",
    "abstain_if_unsupported": False,
    "temperature": 0.3,
}


def load_questions() -> list[dict]:
    with open(QUESTIONS_PATH) as f:
        return [json.loads(line) for line in f]


def run_baseline(retriever_name: str, retriever, questions: list[dict], config: dict) -> list[dict]:
    results = []
    for i, q in enumerate(questions):
        contexts = retriever.retrieve(q["question"], top_k=config["retriever_top_k"])
        answer = generate(q["question"], contexts, temperature=config["temperature"])
        results.append({
            "question_id": q["question_id"],
            "question": q["question"],
            "question_type": q["question_type"],
            "is_answerable": q["is_answerable"],
            "relevant_doc_ids": q["relevant_doc_ids"],
            "expected_answer": q["expected_answer"],
            "retrieved_contexts": contexts,
            "answer": answer,
            "retriever": retriever_name,
            "config": config,
        })
        if (i + 1) % 10 == 0:
            print(f"  [{retriever_name}] {i+1}/100 done")
    return results


def save_run(results: list[dict], retriever_name: str):
    RUNS_DIR.mkdir(exist_ok=True)
    out_path = RUNS_DIR / f"run_{retriever_name}.jsonl"
    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"Saved {len(results)} records → {out_path}")


def main(retriever_names: list[str] = None):
    if retriever_names is None:
        retriever_names = ["bm25", "dense", "hybrid"]

    print("Loading and chunking corpus...")
    chunks = load_and_chunk(str(CORPUS_PATH), BASELINE_CONFIG["chunk_size"], BASELINE_CONFIG["chunk_overlap"])
    print(f"  {len(chunks)} chunks from {CORPUS_PATH}")

    questions = load_questions()
    print(f"  {len(questions)} questions loaded")

    retrievers: dict = {}
    if "bm25" in retriever_names:
        print("Building BM25 index...")
        retrievers["bm25"] = BM25Retriever(chunks)
    if "dense" in retriever_names or "hybrid" in retriever_names:
        print("Building dense index (downloading model if needed)...")
        dense = DenseRetriever(chunks)
        if "dense" in retriever_names:
            retrievers["dense"] = dense
        if "hybrid" in retriever_names:
            from .hybrid_retriever import HybridRetriever as _Hybrid
            hybrid = _Hybrid.__new__(_Hybrid)
            hybrid.chunks = chunks
            hybrid.bm25 = BM25Retriever(chunks)
            hybrid.dense = dense
            retrievers["hybrid"] = hybrid

    for name, retriever in retrievers.items():
        print(f"\nRunning {name} baseline...")
        t0 = time.time()
        results = run_baseline(name, retriever, questions, BASELINE_CONFIG)
        elapsed = time.time() - t0
        save_run(results, name)
        print(f"  Done in {elapsed:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--retriever", choices=["bm25", "dense", "hybrid"], default=None,
                        help="Run a single baseline (default: all 3)")
    args = parser.parse_args()
    names = [args.retriever] if args.retriever else None
    main(names)
