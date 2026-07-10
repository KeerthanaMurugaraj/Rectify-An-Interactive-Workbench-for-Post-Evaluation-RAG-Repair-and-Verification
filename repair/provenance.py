from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

_CET = ZoneInfo("Europe/Berlin")
from pathlib import Path
from typing import Any

from repair.models import RepairCard

PROVENANCE_PATH = Path("repair_provenance.json")


def _load() -> list[dict]:
    if PROVENANCE_PATH.exists():
        return json.loads(PROVENANCE_PATH.read_text())
    return []


def _save(records: list[dict]) -> None:
    PROVENANCE_PATH.write_text(json.dumps(records, indent=2))


def log_approval(
    card: RepairCard,
    approved_by: str,
    approved_params: list[dict[str, Any]] | None = None,
    scope: str = "slice",
    notes: str = "",
) -> dict:
    record = {
        "card_id": card.card_id,
        "slice_type": card.slice_type.value,
        "slice_label": card.slice_label,
        "family": card.family.value,
        "label": card.label,
        "pipeline_stage": card.pipeline_stage,
        "approved_by": approved_by,
        "approved_at": datetime.now(_CET).isoformat(),
        "scope": scope,
        "params": approved_params or [p.model_dump() for p in card.params],
        "affected_cases": card.affected_cases,
        "confidence": card.confidence,
        "expected_benefit": card.expected_benefit,
        "expected_tradeoff": card.expected_tradeoff,
        "notes": notes,
        "action": "approved",
    }
    records = _load()
    records.append(record)
    _save(records)
    return record


def log_rejection(card: RepairCard, rejected_by: str, reason: str = "") -> dict:
    record = {
        "card_id": card.card_id,
        "slice_type": card.slice_type.value,
        "slice_label": card.slice_label,
        "family": card.family.value,
        "label": card.label,
        "rejected_by": rejected_by,
        "rejected_at": datetime.now(_CET).isoformat(),
        "reason": reason,
        "action": "rejected",
        "status": "closed",
    }
    records = _load()
    records.append(record)
    _save(records)
    return record


def is_closed(card_id: str) -> bool:
    """Return True if the card has been closed (rejected/satisfied) and not re-opened."""
    records = _load()
    closed = False
    for r in records:
        if r.get("card_id") != card_id:
            continue
        if r.get("status") == "closed":
            closed = True
        if r.get("action") == "approved":
            closed = False  # approval re-opens it
    return closed


def reopen(card_id: str) -> bool:
    """Delete the most recent closed record for card_id, re-opening the slice."""
    records = _load()
    for i in reversed(range(len(records))):
        r = records[i]
        if r.get("card_id") == card_id and r.get("status") == "closed":
            records.pop(i)
            _save(records)
            return True
    return False


def get_history() -> list[dict]:
    return _load()


def update_sandbox_result(card_id: str, delta_summary: dict) -> bool:
    """Attach sandbox delta summary to the most recent provenance record for card_id."""
    records = _load()
    for r in reversed(records):
        if r.get("card_id") == card_id:
            r["sandbox_result"] = delta_summary
            _save(records)
            return True
    return False


def delete_record(card_id: str, timestamp: str) -> bool:
    """Delete a single provenance record by card_id + timestamp. Returns True if deleted."""
    records = _load()
    before = len(records)
    records = [
        r for r in records
        if not (
            r.get("card_id") == card_id
            and (r.get("approved_at") or r.get("rejected_at", "")) == timestamp
        )
    ]
    if len(records) < before:
        _save(records)
        return True
    return False
