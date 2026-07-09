"""
capture.py — Rectify trace capture.

Wraps a RAG function to record questions, retrieved contexts, and answers,
then exports them to a JSONL file that feeds directly into the Rectify UI.

Usage:
    from capture import RAGCapture

    capture = RAGCapture()

    @capture.trace
    def my_rag(question: str) -> str:
        contexts = retriever.retrieve(question)
        answer   = generator.generate(question, contexts)
        return answer

    for q in questions:
        my_rag(q)

    capture.export("results.jsonl")

The decorator inspects call arguments for common parameter names:
  question / query / q  → stored as "question"
  contexts / context    → stored as "contexts"
The return value is stored as "answer".

For pipelines that return a dict, the decorator tries keys
"answer", "response", "output" in that order.
"""
from __future__ import annotations

import functools
import inspect
import json
import time
import uuid
from pathlib import Path
from typing import Any, Callable


class RAGCapture:
    def __init__(self):
        self._traces: list[dict] = []

    # ── decorator ─────────────────────────────────────────────────────────────

    def trace(self, fn: Callable) -> Callable:
        """Decorator: wrap a RAG function to capture its inputs and output."""
        sig = inspect.signature(fn)
        param_names = list(sig.parameters.keys())

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # Map positional args to parameter names
            bound: dict[str, Any] = {}
            for name, val in zip(param_names, args):
                bound[name] = val
            bound.update(kwargs)

            question = (
                bound.get("question")
                or bound.get("query")
                or bound.get("q")
                or ""
            )
            contexts_in = (
                bound.get("contexts")
                or bound.get("context")
                or []
            )

            t0 = time.time()
            result = fn(*args, **kwargs)
            latency_ms = round((time.time() - t0) * 1000)

            # Extract answer from result
            if isinstance(result, str):
                answer = result
                contexts_out = contexts_in
            elif isinstance(result, dict):
                answer = (
                    result.get("answer")
                    or result.get("response")
                    or result.get("output")
                    or ""
                )
                contexts_out = result.get("contexts") or result.get("context") or contexts_in
            else:
                answer = str(result)
                contexts_out = contexts_in

            self._traces.append({
                "trace_id":   str(uuid.uuid4()),
                "question":   question,
                "contexts":   contexts_out if isinstance(contexts_out, list) else [contexts_out],
                "answer":     answer,
                "latency_ms": latency_ms,
            })
            return result

        return wrapper

    # ── manual capture ────────────────────────────────────────────────────────

    def record(
        self,
        question: str,
        contexts: list[str],
        answer: str,
        *,
        metadata: dict | None = None,
    ) -> None:
        """Manually record a single RAG turn (use when decorator isn't suitable)."""
        self._traces.append({
            "trace_id": str(uuid.uuid4()),
            "question": question,
            "contexts": contexts,
            "answer":   answer,
            **(metadata or {}),
        })

    # ── export ────────────────────────────────────────────────────────────────

    def export(self, path: str | Path, *, mode: str = "w") -> Path:
        """
        Write captured traces to a JSONL file consumable by Rectify.

        path  — output file path (.jsonl or .json)
        mode  — "w" (overwrite) or "a" (append)
        """
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, mode) as f:
            for trace in self._traces:
                f.write(json.dumps(trace) + "\n")
        return out

    def clear(self) -> None:
        """Reset captured traces."""
        self._traces.clear()

    def __len__(self) -> int:
        return len(self._traces)

    def __repr__(self) -> str:
        return f"RAGCapture({len(self._traces)} trace(s))"


# ── LangChain integration (optional) ─────────────────────────────────────────

class RectifyCallback:
    """
    LangChain callback handler that captures RAG traces into a RAGCapture.

    Usage:
        from capture import RAGCapture, RectifyCallback

        capture  = RAGCapture()
        callback = RectifyCallback(capture)

        chain = RetrievalQA.from_chain_type(..., callbacks=[callback])
        chain.run(questions)

        capture.export("results.jsonl")
    """

    def __init__(self, capture: RAGCapture | None = None):
        self._capture = capture or RAGCapture()
        self._current: dict = {}

    @property
    def capture(self) -> RAGCapture:
        return self._capture

    def on_chain_start(self, serialized, inputs, **kwargs):
        self._current = {"question": inputs.get("query") or inputs.get("question", "")}

    def on_retriever_end(self, documents, **kwargs):
        self._current["contexts"] = [
            getattr(d, "page_content", str(d)) for d in (documents or [])
        ]

    def on_chain_end(self, outputs, **kwargs):
        answer = outputs.get("result") or outputs.get("answer") or outputs.get("output", "")
        if self._current.get("question"):
            self._capture.record(
                question=self._current.get("question", ""),
                contexts=self._current.get("contexts", []),
                answer=answer,
            )
        self._current = {}

    # LangChain requires these even if unused
    def on_llm_start(self, *a, **kw): pass
    def on_llm_end(self, *a, **kw): pass
    def on_llm_error(self, *a, **kw): pass
    def on_chain_error(self, *a, **kw): pass
    def on_tool_start(self, *a, **kw): pass
    def on_tool_end(self, *a, **kw): pass
    def on_tool_error(self, *a, **kw): pass
    def on_retriever_start(self, *a, **kw): pass
    def on_retriever_error(self, *a, **kw): pass
    def on_text(self, *a, **kw): pass
    def on_agent_action(self, *a, **kw): pass
    def on_agent_finish(self, *a, **kw): pass


# ── LlamaIndex integration (optional) ────────────────────────────────────────

class RectifyEventHandler:
    """
    LlamaIndex event handler that captures RAG traces into a RAGCapture.

    Usage:
        from capture import RAGCapture, RectifyEventHandler
        from llama_index.core import Settings
        from llama_index.core.callbacks import CallbackManager

        capture = RAGCapture()
        handler = RectifyEventHandler(capture)
        Settings.callback_manager = CallbackManager([handler])

        for q in questions:
            query_engine.query(q)

        capture.export("results.jsonl")
    """

    def __init__(self, capture: RAGCapture | None = None):
        self._capture = capture or RAGCapture()
        self._current: dict = {}

    @property
    def capture(self) -> RAGCapture:
        return self._capture

    def on_event_start(self, event_type, payload=None, **kwargs):
        if payload is None:
            return
        if event_type == "query":
            self._current["question"] = str(payload.get("query_str", ""))
        elif event_type == "retrieve":
            pass  # contexts captured on end

    def on_event_end(self, event_type, payload=None, **kwargs):
        if payload is None:
            return
        if event_type == "retrieve":
            nodes = payload.get("nodes") or []
            self._current["contexts"] = [
                getattr(n, "text", str(n)) for n in nodes
            ]
        elif event_type == "synthesize":
            response = payload.get("response")
            answer = getattr(response, "response", str(response) if response else "")
            if self._current.get("question"):
                self._capture.record(
                    question=self._current.get("question", ""),
                    contexts=self._current.get("contexts", []),
                    answer=answer,
                )
            self._current = {}

    def start_trace(self, *a, **kw): pass
    def end_trace(self, *a, **kw): pass
