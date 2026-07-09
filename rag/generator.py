"""
Generator using a local Ollama model.
Requires Ollama running: `ollama serve`
Default model: mistral:latest
"""
import urllib.request
import json
from typing import List

import os
_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = f"{_OLLAMA_HOST}/api/generate"
DEFAULT_MODEL = "mistral:latest"

_PROMPT_TEMPLATES = {
    "normal": (
        "Answer the question using ONLY the provided context. "
        "If the context does not contain enough information, say \"I don't know.\"\n\n"
        "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    ),
    "grounded": (
        "You must answer ONLY using the information explicitly stated in the context below. "
        "Do NOT infer, guess, or add any information not directly supported by the context. "
        "Do NOT infer dates, causal connections, or entity details not stated. "
        "If the context does not contain enough information, say \"I don't know.\"\n\n"
        "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    ),
    "citation_only": (
        "Answer the question by quoting the relevant part of the context verbatim, "
        "then state your answer. Only use information explicitly present in the context. "
        "Format: Quote: \"...\" → Answer: ...\n\n"
        "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    ),
    "multi_step": (
        "Answer the question step by step. For each step, cite which context chunk supports it. "
        "Cover every part of the question. "
        "If a part cannot be answered from the context, say so explicitly.\n\n"
        "Context:\n{context}\n\nQuestion: {question}\n\nStep-by-step answer:"
    ),
    "structured_output": (
        "Answer the question in a clear, structured format. "
        "Use short sentences. Cover all key points from the context. "
        "Only include information supported by the context.\n\n"
        "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    ),
    "abstain_aware": (
        "Answer the question using ONLY the provided context. "
        "If the context does not contain sufficient information, respond with exactly: "
        "\"I don't know — the context does not contain enough information to answer this question.\" "
        "Do not guess or infer.\n\n"
        "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    ),
    "explicit_citation": (
        "Before answering, list the context chunks you will use. "
        "Then answer using ONLY those chunks. Do not add information from outside the context.\n\n"
        "Context:\n{context}\n\nQuestion: {question}\n\n"
        "Relevant chunks: [list chunk numbers]\nAnswer:"
    ),
}


def generate(
    question: str,
    contexts: List[str],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    prompt_mode: str = "normal",
    abstain_if_unsupported: bool = False,
) -> str:
    context_text = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))

    # abstain_if_unsupported overrides to the abstain_aware template
    effective_mode = "abstain_aware" if abstain_if_unsupported else prompt_mode
    template = _PROMPT_TEMPLATES.get(effective_mode, _PROMPT_TEMPLATES["normal"])
    prompt = template.format(context=context_text, question=question)

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }).encode()

    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    return result["response"].strip()
