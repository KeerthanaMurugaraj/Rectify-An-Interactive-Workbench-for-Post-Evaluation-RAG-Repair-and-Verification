from __future__ import annotations

import os
from repair.models import RepairCard, Slice


def explain_slice(sl: Slice, card: RepairCard | None = None) -> str:
    """
    Call Claude Haiku to produce a natural-language explanation of the slice.
    Returns a plain string. Falls back to a deterministic summary if no API key.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_explanation(sl, card)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        case_snippets = "\n".join(
            f"- [{sc.case.case_id}] Q: {sc.case.question[:80]} | "
            f"faith={sc.case.scores.strict_faithfulness:.2f} "
            f"ret={sc.case.scores.retrieval_relevance:.2f} "
            f"comp={sc.case.scores.answer_completeness:.2f}"
            for sc in sl.cases[:5]
        )

        card_summary = ""
        if card:
            params = ", ".join(f"{p.name}→{p.suggested_value}" for p in card.params)
            card_summary = f"\nProposed repair: {card.label}\nParams: {params}\nBenefit: {card.expected_benefit}\nTradeoff: {card.expected_tradeoff}"

        prompt = f"""You are analyzing a RAG pipeline failure slice for a researcher.

Slice: {sl.slice_label}
Family: {sl.family.value}
Cases ({sl.size} total), sample:
{case_snippets}

Average scores: {sl.avg_scores}
{card_summary}

Write a 3–4 sentence explanation:
1. Why these cases were grouped together (shared pattern)
2. The likely root cause in plain language
3. Why the proposed repair addresses it (if a repair card is provided)

Be specific and concise. Do not use bullet points."""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    except Exception as exc:
        return _fallback_explanation(sl, card) + f"\n\n*(Agent unavailable: {exc})*"


def _fallback_explanation(sl: Slice, card: RepairCard | None) -> str:
    lines = [
        f"**{sl.slice_label}** ({sl.family.value} family, {sl.size} cases)",
        f"Avg scores — faithfulness: {sl.avg_scores.get('strict_faithfulness', '?'):.2f}, "
        f"retrieval: {sl.avg_scores.get('retrieval_relevance', '?'):.2f}, "
        f"completeness: {sl.avg_scores.get('answer_completeness', '?'):.2f}",
    ]
    if card:
        lines.append(f"Repair: {card.label} | Benefit: {card.expected_benefit}")
    return "  \n".join(lines)
