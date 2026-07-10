"""HTML report generator for a Rectify diagnosis + repair session."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from repair.models import EvalCase, RepairSlice, FailureFamily
from repair.clustering import slice_cases, build_slices
from repair.root_cause import infer_root_cause
from repair.repair_planner import build_repair_card
from repair.provenance import get_history


_FAM_COLOR = {
    "retrieval":  "#DBEAFE",
    "grounding":  "#FEF3C7",
    "generation": "#EDE9FE",
    "abstention": "#FFE4E6",
    "none":       "#DCFCE7",
}
_FAM_FG = {
    "retrieval":  "#1E40AF",
    "grounding":  "#92400E",
    "generation": "#5B21B6",
    "abstention": "#9F1239",
    "none":       "#166534",
}
_SCORE_COLOR = lambda v: "#DCFCE7" if v >= 0.7 else ("#FEF9C3" if v >= 0.5 else "#FFE4E6")
_SCORE_FG    = lambda v: "#166534" if v >= 0.7 else ("#854D0E" if v >= 0.5 else "#9F1239")


def _pill(label: str, value: float) -> str:
    bg = _SCORE_COLOR(value)
    fg = _SCORE_FG(value)
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:999px;'
        f'font-size:0.78rem;font-weight:600;margin:2px">{label}: {value:.2f}</span>'
    )


def _badge(family: str) -> str:
    bg = _FAM_COLOR.get(family, "#F0EBE3")
    fg = _FAM_FG.get(family, "#3B2008")
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 10px;border-radius:999px;'
        f'font-size:0.72rem;font-weight:700;letter-spacing:0.04em;text-transform:uppercase">'
        f'{family}</span>'
    )


def generate_html_report(
    eval_path: Path,
    cases: list[EvalCase],
    title: str | None = None,
) -> str:
    sliced  = slice_cases(cases)
    slices  = build_slices(sliced)
    failure = [s for s in slices if s.slice_type != RepairSlice.none]
    healthy = next((s.size for s in slices if s.slice_type == RepairSlice.none), 0)
    title   = title or f"Rectify Report — {eval_path.name}"
    now     = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Load delta files if any
    delta_dir   = Path("evals/deltas")
    delta_files = {p.stem: json.loads(p.read_text()) for p in delta_dir.glob("*.json")} \
                  if delta_dir.exists() else {}

    # Load provenance
    history = get_history()

    # ── CSS ──────────────────────────────────────────────────────────────────
    css = """
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #FAF6F0; color: #3B2008; margin: 0; padding: 0; }
    .page { max-width: 960px; margin: 0 auto; padding: 32px 24px 64px; }
    h1 { font-size: 2rem; font-weight: 900; color: #3B2008; margin-bottom: 4px; }
    h2 { font-size: 1.3rem; font-weight: 800; color: #3B2008; margin: 32px 0 12px;
         border-bottom: 2px solid #D4C5A9; padding-bottom: 6px; }
    h3 { font-size: 1rem; font-weight: 700; color: #5C3D1E; margin: 20px 0 8px; }
    .meta { font-size: 0.82rem; color: #7A5C3A; margin-bottom: 24px; }
    .card { background: #fff; border-radius: 12px; padding: 16px 20px;
            box-shadow: 0 1px 6px rgba(0,0,0,0.07); margin-bottom: 14px; }
    .stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
                 margin-bottom: 20px; }
    .stat-box { background: #fff; border-radius: 10px; padding: 14px 16px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.06); text-align: center; }
    .stat-val { font-size: 2rem; font-weight: 900; color: #3B2008; }
    .stat-lbl { font-size: 0.72rem; color: #7A5C3A; text-transform: uppercase;
                letter-spacing: 0.06em; margin-top: 2px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    th { background: #E8DECE; color: #3B2008; font-weight: 700; padding: 8px 10px;
         text-align: left; }
    td { padding: 7px 10px; border-bottom: 1px solid #EDE8DF; }
    tr:hover td { background: #FAF6F0; }
    .repair-card { background: #F5EDE0; border-left: 4px solid #8B6343;
                   border-radius: 0 12px 12px 0; padding: 14px 18px; margin: 10px 0; }
    .param-row { display: flex; gap: 8px; align-items: center; margin: 6px 0; }
    .param-old { background: #FFE4E6; color: #9F1239; border-radius: 6px;
                 padding: 3px 10px; font-family: monospace; font-size: 0.85rem; }
    .param-new { background: #DCFCE7; color: #166534; border-radius: 6px;
                 padding: 3px 10px; font-family: monospace; font-size: 0.85rem; }
    .param-name { font-size: 0.8rem; color: #7A5C3A; min-width: 160px; }
    .answer-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 8px 0; }
    .answer-box { border-radius: 0 8px 8px 0; padding: 10px 14px;
                  font-size: 0.85rem; line-height: 1.5; }
    .answer-before { background: #FFF7F0; border-left: 3px solid #C4A882; }
    .answer-after-ok  { background: #F0FFF4; border-left: 3px solid #86EFAC; }
    .answer-after-bad { background: #FFF5F5; border-left: 3px solid #FCA5A5; }
    .answer-after-mid { background: #FFF7F0; border-left: 3px solid #C4A882; }
    .verdict-improved  { color: #166534; font-weight: 700; }
    .verdict-regressed { color: #9F1239; font-weight: 700; }
    .verdict-unchanged { color: #7A5C3A; }
    details summary { cursor: pointer; font-weight: 600; color: #5C3D1E;
                      padding: 6px 0; user-select: none; }
    details[open] summary { color: #3B2008; }
    footer { font-size: 0.72rem; color: #A0845C; text-align: center;
             margin-top: 48px; border-top: 1px solid #D4C5A9; padding-top: 16px; }
    """

    # ── Summary stats ─────────────────────────────────────────────────────────
    family_counts: dict[str, int] = {}
    for s in failure:
        family_counts[s.family.value] = family_counts.get(s.family.value, 0) + s.size

    stat_boxes = "".join(
        f'<div class="stat-box"><div class="stat-val">{v}</div>'
        f'<div class="stat-lbl">{k}</div></div>'
        for k, v in [
            ("Total cases",     len(cases)),
            ("Failure slices",  len(failure)),
            ("Failing cases",   sum(s.size for s in failure)),
            ("Healthy cases",   healthy),
        ]
    )

    # ── Family breakdown ──────────────────────────────────────────────────────
    family_rows = "".join(
        f'<tr><td>{_badge(fam)}</td><td>{cnt}</td>'
        f'<td>{cnt/len(cases):.0%}</td></tr>'
        for fam, cnt in sorted(family_counts.items(), key=lambda x: -x[1])
    )
    family_table = f"""
    <table>
      <tr><th>Family</th><th>Cases</th><th>% of total</th></tr>
      {family_rows}
    </table>""" if family_rows else "<p>No failures detected.</p>"

    # ── Failure slices ────────────────────────────────────────────────────────
    slice_sections = ""
    for s in failure:
        cause = infer_root_cause(s)
        card  = build_repair_card(s)
        score_pills = " ".join(
            _pill(m.replace("_", " "), v) for m, v in s.avg_scores.items()
        )

        # Repair card HTML
        repair_html = ""
        if card:
            params_html = "".join(
                f'<div class="param-row">'
                f'<span class="param-name">{p.name}</span>'
                f'<span class="param-old">{p.current_value}</span>'
                f'<span style="color:#A8896C;margin:0 4px">→</span>'
                f'<span class="param-new">{p.suggested_value}</span>'
                f'</div>'
                for p in card.params
            )
            repair_html = f"""
            <div class="repair-card">
              <div style="font-size:0.72rem;font-weight:700;color:#8B6343;
                          text-transform:uppercase;letter-spacing:.05em">Repair Card</div>
              <div style="font-weight:700;font-size:0.95rem;margin:4px 0">{card.label}</div>
              <div style="font-size:0.82rem;color:#7A5C3A">
                Stage: {card.pipeline_stage} &nbsp;·&nbsp;
                Confidence: {card.confidence:.0%} &nbsp;·&nbsp;
                Affects: {card.affected_cases} cases
              </div>
              <div style="margin-top:8px;font-size:0.85rem">{card.expected_benefit}</div>
              <div style="margin-top:10px">{params_html}</div>
            </div>"""

        # Delta results for this card
        delta_html = ""
        if card and card.card_id in delta_files:
            dr   = delta_files[card.card_id]
            summ = dr.get("summary", {})
            avg_d = summ.get("avg_deltas", {})
            delta_rows = "".join(
                f'<tr><td>{m}</td>'
                f'<td>{summ.get("before_avg",{}).get(m,0):.3f}</td>'
                f'<td>{summ.get("after_avg",{}).get(m,0):.3f}</td>'
                f'<td style="color:{"#166534" if v>=0 else "#9F1239"};font-weight:700">'
                f'{v:+.3f}</td></tr>'
                for m, v in avg_d.items()
            )
            delta_html = f"""
            <h3>Sandbox Delta</h3>
            <div style="display:flex;gap:16px;margin-bottom:12px">
              <div class="stat-box" style="flex:1"><div class="stat-val" style="color:#166534">{summ.get('improved',0)}</div><div class="stat-lbl">Improved</div></div>
              <div class="stat-box" style="flex:1"><div class="stat-val">{summ.get('unchanged',0)}</div><div class="stat-lbl">Unchanged</div></div>
              <div class="stat-box" style="flex:1"><div class="stat-val" style="color:#9F1239">{summ.get('regressed',0)}</div><div class="stat-lbl">Regressed</div></div>
              <div class="stat-box" style="flex:1"><div class="stat-val">{summ.get('improvement_rate',0):.0%}</div><div class="stat-lbl">Rate</div></div>
            </div>
            <table>
              <tr><th>Metric</th><th>Before</th><th>After</th><th>Δ</th></tr>
              {delta_rows}
            </table>
            <details style="margin-top:12px">
              <summary>Per-case answers ({len(dr.get('cases',[]))} cases)</summary>
              {''.join(_case_delta_html(c) for c in dr.get('cases', []))}
            </details>"""

        slice_sections += f"""
        <div class="card">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
            <b style="font-size:1rem">{s.slice_label}</b>
            {_badge(s.family.value)}
            <span style="font-size:0.82rem;color:#7A5C3A">n={s.size}</span>
          </div>
          <div style="margin-bottom:8px">{score_pills}</div>
          <div style="background:#F0EBE3;border-radius:8px;padding:10px 14px;
                      font-size:0.85rem;margin-bottom:10px">
            <b>Root cause:</b> {cause['hypothesis']}<br>
            <span style="color:#7A6352">{cause['action']}</span>
          </div>
          {repair_html}
          {delta_html}
        </div>"""

    # ── Provenance log ────────────────────────────────────────────────────────
    prov_rows = ""
    for h in history:
        act = h.get("action", "—")
        icon = "✅" if act == "approved" else "❌"
        ts   = (h.get("approved_at") or h.get("rejected_at", ""))[:19].replace("T", " ")
        by   = h.get("approved_by") or h.get("rejected_by", "—")
        prov_rows += (
            f'<tr><td>{icon}</td><td>{h.get("slice_label","—")}</td>'
            f'<td>{_badge(h.get("family","—"))}</td>'
            f'<td>{act}</td><td>{by}</td><td>{ts}</td></tr>'
        )
    prov_section = f"""
    <h2>Approval History</h2>
    <table>
      <tr><th></th><th>Slice</th><th>Family</th><th>Action</th><th>By</th><th>At</th></tr>
      {prov_rows if prov_rows else '<tr><td colspan="6">No approvals logged yet.</td></tr>'}
    </table>""" if history else ""

    # ── Full HTML ─────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>{css}</style>
</head>
<body>
<div class="page">
  <h1>🔧 {title}</h1>
  <div class="meta">
    Generated: {now} &nbsp;·&nbsp; Eval file: {eval_path.name} &nbsp;·&nbsp;
    Built with <b>Rectify</b> — EMNLP 2026 Demo
  </div>

  <h2>Summary</h2>
  <div class="stat-grid">{stat_boxes}</div>

  <h2>Failure Families</h2>
  {family_table}

  <h2>Failure Slices & Repair Cards</h2>
  {slice_sections if slice_sections else '<p>No failure slices detected.</p>'}

  {prov_section}

  <footer>
    Rectify · RAG Repair Workbench · EMNLP 2026 Demo Track<br>
    Report generated {now}
  </footer>
</div>
</body>
</html>"""

    return html


def _case_delta_html(case: dict) -> str:
    verdict = case.get("verdict", "—")
    icon    = {"improved": "✅", "unchanged": "➖", "regressed": "❌"}.get(verdict, "—")
    after_cls = (
        "answer-after-ok"  if verdict == "improved"  else
        "answer-after-bad" if verdict == "regressed" else
        "answer-after-mid"
    )
    deltas = case.get("deltas", {})
    delta_pills = " ".join(
        f'<span style="background:{"#DCFCE7" if v>=0 else "#FFE4E6"};'
        f'color:{"#166534" if v>=0 else "#9F1239"};padding:2px 7px;'
        f'border-radius:999px;font-size:0.72rem;font-weight:600">'
        f'{m[:10]}: {v:+.2f}</span>'
        for m, v in deltas.items()
    )
    return f"""
    <div style="border:1px solid #E8DECE;border-radius:8px;padding:10px 14px;margin:8px 0">
      <div style="font-weight:700;margin-bottom:4px">{icon} {case.get('case_id','—')}
        <span style="font-weight:400;font-size:0.82rem;color:#7A5C3A;margin-left:8px">
          {case.get('question','')[:100]}…</span></div>
      <div style="margin-bottom:8px">{delta_pills}</div>
      <div class="answer-grid">
        <div>
          <div style="font-size:0.72rem;font-weight:700;color:#7A5C3A;margin-bottom:4px">BEFORE</div>
          <div class="answer-box answer-before">{case.get('before_answer') or '—'}</div>
        </div>
        <div>
          <div style="font-size:0.72rem;font-weight:700;color:#7A5C3A;margin-bottom:4px">AFTER</div>
          <div class="answer-box {after_cls}">{case.get('after_answer') or '—'}</div>
        </div>
      </div>
    </div>"""
