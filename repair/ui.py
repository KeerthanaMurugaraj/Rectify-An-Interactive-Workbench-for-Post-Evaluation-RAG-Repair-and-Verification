from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from repair.clustering import build_slices, slice_cases
from repair.delta_report import compute_delta
from repair.explainer import explain_slice
from repair.loader import load_eval_results
from repair.models import RepairCard, RepairSlice, Slice
from repair.provenance import get_history, is_closed, log_approval, log_rejection, reopen
from repair.repair_planner import _detect_compound
from repair.repair_planner import build_repair_card
from repair.root_cause import infer_root_cause

_BADGE = {
    "retrieval":  ("badge-retrieval",  "🔵"),
    "grounding":  ("badge-grounding",  "🟡"),
    "generation": ("badge-generation", "🟣"),
    "abstention": ("badge-abstention", "🔴"),
    "none":       ("badge-healthy",    "🟢"),
}


def _pills(avg_scores: dict) -> str:
    parts = []
    for m, v in avg_scores.items():
        cls = "score-good" if v >= 0.7 else ("score-warn" if v >= 0.5 else "score-bad")
        parts.append(
            f'<span class="score-pill {cls}">'
            f'{m.replace("_"," ")[:10]}: {v:.2f}</span>'
        )
    return " ".join(parts)


def render_repair_lab(eval_path: Path | None = None):
    st.markdown("## 🛠 Repair Lab")

    if eval_path is None:
        eval_files = sorted(Path("evals").glob("eval_*.json")) if Path("evals").exists() else []
        if not eval_files:
            st.warning("No eval files found in `evals/`. Run `python evaluate.py` first.")
            return
        eval_path = st.selectbox(
            "Eval file",
            eval_files,
            format_func=lambda p: p.name,
            key="repair_eval_sel",
        )

    cases    = load_eval_results(eval_path)
    sliced   = slice_cases(cases)
    slices   = build_slices(sliced)
    failures = [s for s in slices if s.slice_type != RepairSlice.none]

    if not failures:
        st.success("✅ No failure slices detected.")
        return

    def _card_id(s: Slice) -> str:
        base = s.slice_type.value[:16]
        return f"{base}_c" if _detect_compound(s) else base

    open_slices   = [s for s in failures if not is_closed(_card_id(s))]
    closed_slices = [s for s in failures if is_closed(_card_id(s))]

    st.caption(
        f"{len(cases)} cases · **{len(open_slices)} open** / "
        f"{len(closed_slices)} closed slice(s)"
    )

    def _label(s: Slice) -> str:
        _, icon = _BADGE.get(s.family.value, ("", "●"))
        return f"{icon}  {s.slice_label}  (n={s.size})"

    if not open_slices:
        st.success("✅ All failure slices have been closed.")
    else:
        idx = st.selectbox(
            "Select slice to inspect",
            range(len(open_slices)),
            format_func=lambda i: _label(open_slices[i]),
            key="repair_slice_sel",
        )
        sl: Slice = open_slices[idx]

        st.divider()
        _render_slice_panel(sl, eval_path)

    if closed_slices:
        with st.expander(f"✅ Closed slices ({len(closed_slices)}) — satisfied with current results", expanded=False):
            for i, s in enumerate(closed_slices):
                _, icon = _BADGE.get(s.family.value, ("", "●"))
                col_lbl, col_btn = st.columns([5, 1])
                col_lbl.markdown(f"{icon} **{s.slice_label}** (n={s.size})")
                if col_btn.button("↩ Reopen", key=f"reopen_{_card_id(s)}_{i}"):
                    reopen(_card_id(s))
                    st.rerun()


def _render_slice_panel(sl: Slice, eval_path: Path | None = None):
    secondary_families = sorted({
        sc.secondary_family.value
        for sc in sl.cases
        if sc.secondary_family is not None
    })
    badge_cls, icon = _BADGE.get(sl.family.value, ("", "●"))

    # Header
    col_h, col_b = st.columns([6, 1])
    col_h.markdown(f"### {icon} {sl.slice_label}")
    col_b.markdown(
        f'<div style="padding-top:8px">'
        f'<span class="badge {badge_cls}">{sl.family.value}</span></div>',
        unsafe_allow_html=True,
    )

    if secondary_families:
        n_compound = sum(1 for sc in sl.cases if sc.secondary_family)
        sec = " + ".join(secondary_families)
        st.info(
            f"⚠️ **Compound failure** — {n_compound}/{sl.size} cases also show "
            f"**{sec}** signals. The repair card addresses both layers."
        )

    # Scores
    st.markdown("**Average scores in this slice**")
    cols = st.columns(len(sl.avg_scores))
    for col, (metric, val) in zip(cols, sl.avg_scores.items()):
        col.metric(
            metric.replace("_", " ").title(),
            f"{val:.2f}",
            delta_color="normal" if val >= 0.7 else ("off" if val >= 0.5 else "inverse"),
        )

    # Root cause card
    cause = infer_root_cause(sl)
    st.markdown(
        f'<div class="card" style="margin-top:12px">'
        f'<span style="font-size:0.78rem;font-weight:700;color:var(--text-accent);'
        f'text-transform:uppercase;letter-spacing:.05em">Root cause</span><br>'
        f'<span style="font-weight:600;color:var(--text-h)">{cause["hypothesis"]}</span><br>'
        f'<span style="color:var(--text-secondary);font-size:0.9rem">{cause["action"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # AI Explanation
    card = build_repair_card(sl)
    with st.expander("🤖 AI Explanation (Claude Haiku)", expanded=False):
        key = f"explanation_{sl.slice_type.value}"
        if key not in st.session_state:
            st.session_state[key] = None
        if st.button("Generate explanation", key=f"explain_btn_{sl.slice_type.value}"):
            with st.spinner("Asking Claude Haiku…"):
                st.session_state[key] = explain_slice(sl, card)
        if st.session_state[key]:
            st.markdown(st.session_state[key])
        else:
            st.caption("Click **Generate explanation** for a natural-language summary. Requires `ANTHROPIC_API_KEY`.")

    # Cases in slice
    with st.expander(f"📋 Cases in this slice ({sl.size})", expanded=False):
        for sc in sl.cases:
            s = sc.case.scores
            d = sc.case.diagnostics
            st.markdown(
                f'<div class="card" style="margin-bottom:8px">'
                f'<b>{sc.case.case_id}</b> &nbsp;·&nbsp; '
                f'<span style="color:var(--text-case)">{sc.case.question[:90]}…</span><br>'
                f'<div style="margin-top:6px">{_pills({"faith": s.strict_faithfulness, "ret": s.retrieval_relevance, "comp": s.answer_completeness, "util": s.context_utilization, "coh": s.coherence})}</div>'
                f'<div style="margin-top:4px;font-size:0.78rem;color:var(--text-muted)">'
                f'hallucinations={d.n_hallucinated} &nbsp; unused_chunks={d.n_unused_chunks} &nbsp; uncovered_aspects={d.n_uncovered_aspects}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    st.divider()

    if card is None:
        st.info("No repair template available for this slice type.")
        return

    _render_repair_card(card, sl, eval_path)


def _render_repair_card(card: RepairCard, sl: Slice, eval_path: Path | None = None):
    st.markdown("### 🔧 Repair Card")

    # conf_color = "#16A34A" if card.confidence >= 0.7 else ("#D97706" if card.confidence >= 0.5 else "#DC2626")
    # st.markdown(
    #     f'<div class="repair-card">'
    #     f'<div style="font-size:1.05rem;font-weight:700;color:var(--text-h)">{card.label}</div>'
    #     f'<div style="margin-top:5px;font-size:0.85rem;color:var(--text-secondary)">'
    #     f'Stage: <code>{card.pipeline_stage}</code> &nbsp;·&nbsp; '
    #     f'<span style="color:{conf_color};font-weight:600">{card.confidence:.0%} confidence</span>'
    #     f' &nbsp;·&nbsp; {len(card.affected_cases)} case(s) affected'
    #     f'</div></div>',
    #     unsafe_allow_html=True,
    # )

    if card.rationale:
        st.markdown(f"> {card.rationale}")

    col_b, col_t = st.columns(2)
    col_b.success(f"**Benefit:** {card.expected_benefit}")
    col_t.warning(f"**Trade-off:** {card.expected_tradeoff}")

    if card.repair_type == "advisory":
        st.warning("This slice requires manual inspection — no automated config patch is proposed.")
        _log_buttons(card, sl, [], scope_key=f"scope_{card.card_id}", eval_path=eval_path)
        return

    # Parameter changes
    _PROMPT_MODES = [
        "normal", "grounded", "citation_only", "multi_step",
        "structured_output", "abstain_aware", "explicit_citation",
    ]

    st.markdown("**Parameter changes** *(edit suggested values before approving)*")
    edited_params: list[dict[str, Any]] = []
    for param in card.params:
        c_name, c_cur, c_arrow, c_new = st.columns([3, 2, 0.4, 2])
        c_name.markdown(
            f"**`{param.name}`**  \n"
            f"<small style='color:var(--text-secondary)'>{param.description}</small>",
            unsafe_allow_html=True,
        )
        c_cur.markdown(
            f'<div class="param-current">'
            f'<div style="font-size:0.7rem;color:#9F1239;margin-bottom:2px">current</div>'
            f'{param.current_value}</div>',
            unsafe_allow_html=True,
        )
        c_arrow.markdown(
            '<div class="param-arrow">→</div>',
            unsafe_allow_html=True,
        )

        key = f"param_{card.card_id}_{param.name}"
        if param.name == "prompt_mode":
            default_idx = _PROMPT_MODES.index(param.suggested_value) if param.suggested_value in _PROMPT_MODES else 0
            new_val = c_new.selectbox("Suggested", _PROMPT_MODES, index=default_idx, key=key, label_visibility="visible")
        elif param.name in ("reranker_enabled", "abstain_if_unsupported"):
            new_val = c_new.toggle("Enable", value=bool(param.suggested_value), key=key)
        elif param.name == "temperature":
            new_val = c_new.slider("Suggested", min_value=0.0, max_value=1.0, step=0.05,
                                   value=float(param.suggested_value), key=key, label_visibility="visible")
        elif param.name == "retriever_top_k":
            new_val = c_new.number_input("Suggested", min_value=1, max_value=20, step=1,
                                         value=int(param.suggested_value), key=key, label_visibility="visible")
        elif param.name in ("chunk_size", "chunk_overlap"):
            new_val = c_new.number_input("Suggested", min_value=0, max_value=1000, step=10,
                                         value=int(param.suggested_value), key=key, label_visibility="visible")
        else:
            new_val = c_new.text_input("Suggested", value=str(param.suggested_value),
                                       key=key, label_visibility="visible")
            new_val = _coerce(new_val, param.suggested_value)

        edited_params.append({
            "name": param.name,
            "current_value": param.current_value,
            "suggested_value": new_val,
            "description": param.description,
        })

    st.divider()
    _log_buttons(card, sl, edited_params, scope_key=f"scope_{card.card_id}", eval_path=eval_path)

    with st.expander("📜 Approval history for this card", expanded=False):
        from repair.provenance import delete_record
        history = [h for h in get_history() if h.get("card_id") == card.card_id]
        if not history:
            st.caption("No approvals logged yet for this card.")
        else:
            _ACT_ICON = {"approved": "✅", "rejected": "❌"}
            for h in history:
                ts  = h.get("approved_at") or h.get("rejected_at", "")
                by  = h.get("approved_by") or h.get("rejected_by", "—")
                act = h.get("action", "—")
                c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
                c1.markdown(f"{_ACT_ICON.get(act, '—')} **{act.title()}**")
                c2.markdown(f"By **{by}**")
                c3.markdown(f"`{ts[:19]}`")
                if c4.button("🗑", key=f"del_card_{card.card_id}_{ts}", help="Delete this entry"):
                    if delete_record(card.card_id, ts):
                        st.rerun()
                    else:
                        st.error("Could not delete entry.")


def _log_buttons(card: RepairCard, sl: Slice, edited_params: list[dict], scope_key: str, eval_path: Path | None = None):
    col_scope, col_name = st.columns(2)
    with col_scope:
        scope = st.radio(
            "Apply repair to",
            ["Entire slice", "Single case"],
            horizontal=True,
            key=scope_key,
        )
    with col_name:
        approver = st.text_input(
            "Your name / ID",
            key=f"approver_{card.card_id}",
            placeholder="e.g. user_name",
        )

    case_id_filter: str | None = None
    if scope == "Single case":
        case_id_filter = st.selectbox(
            "Select case",
            [sc.case.case_id for sc in sl.cases],
            key=f"case_sel_{card.card_id}",
        )

    notes = st.text_area("Notes (optional)", key=f"notes_{card.card_id}", height=60)

    col_a, col_r, col_s = st.columns(3)

    if col_a.button("✅ Approve", key=f"approve_{card.card_id}", use_container_width=True):
        if not approver.strip():
            st.error("Enter your name / ID before approving.")
        else:
            log_approval(
                card,
                approved_by=approver,
                approved_params=edited_params,
                scope="single" if scope == "Single case" else "slice",
                notes=notes,
            )
            st.success("Repair approved and logged to `repair_provenance.json` ✅")
            st.rerun()

    if col_r.button("✅ Close (satisfied)", key=f"reject_{card.card_id}", use_container_width=True):
        log_rejection(card, rejected_by=approver or "anonymous", reason=notes)
        st.success("Slice closed — marked as satisfied with current results.")
        st.rerun()

    if col_s.button("▶ Run Sandbox", key=f"sandbox_{card.card_id}", use_container_width=True):
        _run_sandbox_inline(card, sl, edited_params, case_id_filter, eval_path)

    # Render persisted results if available for this card
    _render_sandbox_results(card.card_id)


def _run_sandbox_inline(
    card: RepairCard,
    sl: Slice,
    edited_params: list[dict],
    case_id_filter: str | None,
    eval_path: Path | None = None,
):
    from repair.sandbox_runner import run_sandbox

    patched_config = {p["name"]: p["suggested_value"] for p in edited_params}
    before_cases = [sc.case for sc in sl.cases]
    if case_id_filter:
        before_cases = [c for c in before_cases if c.case_id == case_id_filter]

    with st.status(f"Running sandbox on {len(before_cases)} case(s)…", expanded=True) as status:
        st.write("Rerunning RAG pipeline with patched config…")
        try:
            after_cases = run_sandbox(before_cases, patched_config, backend="ragvue")
            status.update(label="Sandbox complete ✅", state="complete")
        except Exception as exc:
            status.update(label="Sandbox failed", state="error")
            st.error(f"Sandbox error: {exc}")
            return

    report = compute_delta(
        before_cases, after_cases,
        card_id=card.card_id,
        cluster_type=sl.slice_type.value,
        family=sl.family.value,
    )

    from repair.provenance import update_sandbox_result
    update_sandbox_result(card.card_id, {
        "n_cases":          report.n_cases,
        "improved":         len(report.improved),
        "unchanged":        len(report.unchanged),
        "regressed":        len(report.regressed),
        "improvement_rate": report.improvement_rate,
        "avg_deltas":       report.avg_deltas,
    })

    # Persist per-case deltas to evals/deltas/ for the Delta Explorer tab
    import json
    from datetime import datetime
    from zoneinfo import ZoneInfo
    _b_idx = {c.case_id: c for c in before_cases}
    _a_idx = {c.case_id: c for c in after_cases}
    delta_dir = Path("evals/deltas")
    delta_dir.mkdir(parents=True, exist_ok=True)
    _ts_suffix = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y%m%dT%H%M%S")
    (delta_dir / f"{card.card_id}_{_ts_suffix}.json").write_text(json.dumps({
        "card_id":     card.card_id,
        "slice_label": sl.slice_label,
        "family":      sl.family.value,
        "eval_file":   eval_path.name if eval_path else "",
        "ran_at":      datetime.now(ZoneInfo("Europe/Berlin")).isoformat(),
        "summary": {
            "n_cases":          report.n_cases,
            "improved":         len(report.improved),
            "unchanged":        len(report.unchanged),
            "regressed":        len(report.regressed),
            "improvement_rate": report.improvement_rate,
            "before_avg":       report.before_avg,
            "after_avg":        report.after_avg,
            "avg_deltas":       report.avg_deltas,
        },
        "cases": [
            {
                "case_id":       cd.case_id,
                "verdict":       cd.verdict,
                "question":      _b_idx[cd.case_id].question if cd.case_id in _b_idx else "",
                "before_answer":   _b_idx[cd.case_id].answer    if cd.case_id in _b_idx else "",
                "after_answer":    _a_idx[cd.case_id].answer    if cd.case_id in _a_idx else "",
                "before_contexts": _b_idx[cd.case_id].contexts  if cd.case_id in _b_idx else [],
                "after_contexts":  _a_idx[cd.case_id].contexts  if cd.case_id in _a_idx else [],
                "before_scores": cd.before,
                "after_scores":  cd.after,
                "deltas":        cd.deltas,
            }
            for cd in report.case_deltas
        ],
    }, indent=2))

    # Persist results in session state so they survive rerenders
    st.session_state[f"sandbox_result_{card.card_id}"] = {
        "report":       report,
        "before_cases": before_cases,
        "after_cases":  after_cases,
    }


def _render_sandbox_results(card_id: str):
    key = f"sandbox_result_{card_id}"
    if key not in st.session_state:
        return

    import pandas as pd
    data         = st.session_state[key]
    report       = data["report"]
    before_cases = data["before_cases"]
    after_cases  = data["after_cases"]

    st.divider()
    st.markdown("### 📊 Before / After Results")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Improved",         len(report.improved),
              delta=f"+{len(report.improved)}", delta_color="normal")
    c2.metric("Unchanged",        len(report.unchanged))
    c3.metric("Regressed",        len(report.regressed),
              delta=f"-{len(report.regressed)}", delta_color="inverse")
    c4.metric("Improvement rate", f"{report.improvement_rate:.0%}")

    delta_df = pd.DataFrame({
        "metric": list(report.avg_deltas.keys()),
        "before": [report.before_avg[m] for m in report.avg_deltas],
        "after":  [report.after_avg[m]  for m in report.avg_deltas],
        "Δ":      list(report.avg_deltas.values()),
    })

    col_chart, col_tbl = st.columns([3, 2])
    with col_chart:
        st.markdown("**Before vs After**")
        st.bar_chart(delta_df.set_index("metric")[["before", "after"]], height=260)
    with col_tbl:
        st.markdown("**Score deltas**")
        disp = delta_df[["metric", "before", "after", "Δ"]].copy()
        disp["before"] = disp["before"].map("{:.2f}".format)
        disp["after"]  = disp["after"].map("{:.2f}".format)
        disp["Δ"]      = disp["Δ"].map("{:+.2f}".format)
        st.table(disp.set_index("metric"))

    st.markdown("**Per-case verdicts**")
    _V = {"improved": "✅", "unchanged": "➖", "regressed": "❌"}
    rows = [
        {
            "":        _V.get(cd.verdict, "—"),
            "case_id": cd.case_id,
            "verdict": cd.verdict,
            **{f"Δ{m[:8]}": f"{cd.deltas[m]:+.2f}" for m in cd.deltas},
        }
        for cd in report.case_deltas
    ]
    st.table(pd.DataFrame(rows).set_index("case_id"))

    st.markdown("**Answer comparison**")
    before_by_id = {c.case_id: c for c in before_cases}
    after_by_id  = {c.case_id: c for c in after_cases}
    for cd in report.case_deltas:
        b = before_by_id.get(cd.case_id)
        a = after_by_id.get(cd.case_id)
        if not b or not a:
            continue
        icon = _V.get(cd.verdict, "—")
        with st.expander(f"{icon} {cd.case_id}", expanded=False):
            st.markdown(f"**Question:** {b.question}")
            if b.expected_answer:
                st.markdown(f"**Expected:** {b.expected_answer}")
            st.divider()
            col_b, col_a = st.columns(2)
            with col_b:
                st.markdown("**Before**")
                st.markdown(
                    f'<div style="background:var(--bg-answer);border-left:3px solid var(--border-answer);'
                    f'padding:10px 14px;border-radius:0 8px 8px 0;font-size:0.88rem;'
                    f'line-height:1.5;color:var(--text-primary)">{b.answer or "<em>no answer</em>"}</div>',
                    unsafe_allow_html=True,
                )
            with col_a:
                st.markdown("**After**")
                border_color = "#86EFAC" if cd.verdict == "improved" else ("#FCA5A5" if cd.verdict == "regressed" else "var(--border-answer)")
                after_bg = "var(--bg-gold)" if cd.verdict == "improved" else "var(--bg-answer)"
                st.markdown(
                    f'<div style="background:{after_bg};border-left:3px solid {border_color};'
                    f'padding:10px 14px;border-radius:0 8px 8px 0;font-size:0.88rem;'
                    f'line-height:1.5;color:var(--text-primary)">{a.answer or "<em>no answer</em>"}</div>',
                    unsafe_allow_html=True,
                )

    if st.button("🗑 Clear results", key=f"clear_{card_id}"):
        del st.session_state[key]
        st.rerun()


def _coerce(text: str, reference: Any) -> Any:
    if isinstance(reference, bool):
        return text.lower() in ("true", "1", "yes")
    if isinstance(reference, int):
        try:
            return int(text)
        except ValueError:
            return reference
    if isinstance(reference, float):
        try:
            return float(text)
        except ValueError:
            return reference
    return text
