import streamlit as st

st.set_page_config(
    page_title="Rectify — RAG Repair Workbench",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme ──────────────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
_dark = st.session_state["dark_mode"]

def _v(light, dark):
    return dark if _dark else light

_vars = {
    "text-primary":    _v("#3B2008", "#EEE0CC"),
    "text-h":          _v("#3B2A1A", "#EEE0CC"),
    "text-secondary":  _v("#7A5C3A", "#C4956A"),
    "text-muted":      _v("#A0845C", "#8A6C4A"),
    "text-accent":     _v("#8B6343", "#D4956A"),
    "text-case":       _v("#5C3D1E", "#C4956A"),
    "text-h4":         _v("#6B3A12", "#D4956A"),
    "bg-card":         _v("#FAF6F0", "#2A2018"),
    "bg-card-muted":   _v("#F0EBE3", "#322820"),
    "bg-repair-card":  _v("#F5EDE0", "#2E2418"),
    "bg-answer":       _v("#FFF7F0", "#241810"),
    "bg-gold":         _v("#F0FFF4", "#122018"),
    "bg-pipe-stage":   _v("#E8DECE", "#332820"),
    "bg-ticker":       _v("#E8DDD0", "#251C14"),
    "bg-step-num":     _v("#E8DECE", "#332820"),
    "bg-label":        _v("#FAF6F0", "#2A2018"),
    "bg-sidebar-card": _v("#FAF6F0", "#2A2018"),
    "border":          _v("#D4C5A9", "#4A3828"),
    "border-answer":   _v("#C4A882", "#6A4C28"),
    "border-accent":   _v("#8B6343", "#D4956A"),
    "arrow":           _v("#C4A882", "#8A6C4A"),
    "ticker-text":     _v("#6B4C2A", "#C4956A"),
    "ticker-sep":      _v("#C4A882", "#8A6C4A"),
    "pipe-text":       _v("#3B2008", "#EEE0CC"),
    "pipe-desc":       _v("#A0845C", "#8A6C4A"),
}
_css_vars = "\n".join(f"  --{k}: {val};" for k, val in _vars.items())

_dark_overrides = (
    """
/* Page & container backgrounds */
[data-testid="stApp"],[data-testid="stAppViewContainer"],[data-testid="stMain"],section.main,.main { background-color: #1C1510 !important; }
.block-container { background-color: #1C1510 !important; }
section[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child { background-color: #1C1510 !important; }
[data-testid="stVerticalBlockBorderWrapper"],[data-testid="stVerticalBlock"] { background-color: transparent !important; }
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stAppHeader"] { background-color: #1C1510 !important; }
header { background-color: #1C1510 !important; }
header button { background-color: transparent !important; border-color: #4A3828 !important; color: #EEE0CC !important; }
header button:hover { background-color: #2A2018 !important; }
header button *,header button svg,header button svg path { color: #EEE0CC !important; fill: #EEE0CC !important; }
header a,header span,header p { color: #EEE0CC !important; }

/* Tabs */
[data-baseweb="tab-list"] { background-color: #251C14 !important; border-color: #4A3828 !important; }
[data-baseweb="tab"] { color: #C4956A !important; }
[data-baseweb="tab"][aria-selected="true"] { color: #EEE0CC !important; border-bottom-color: #D4956A !important; }
[data-baseweb="tab-panel"] { background-color: #1C1510 !important; }

/* Headings */
h1, h2, h3, h4, h5, h6 { color: #EEE0CC !important; }
[data-testid="stHeading"],[data-testid="stHeading"] span,.stHeadingWithActionElements,.stHeadingWithActionElements span { color: #EEE0CC !important; }

/* Markdown text */
[data-testid="stMarkdownContainer"] { color: #EEE0CC; }
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] strong,[data-testid="stMarkdownContainer"] em,
[data-testid="stMarkdownContainer"] td,[data-testid="stMarkdownContainer"] th { color: #EEE0CC; }
[data-testid="stMarkdownContainer"] a { color: #D4956A !important; }
[data-testid="stMarkdownContainer"] code { background-color: #2A2018 !important; color: #D4956A !important; }
[data-testid="stMarkdownContainer"] pre { background-color: #2A2018 !important; }

/* st.table() */
[data-testid="stTable"] table { background-color: #2A2018 !important; border-color: #4A3828 !important; }
[data-testid="stTable"] th { background-color: #322820 !important; color: #EEE0CC !important; border-color: #4A3828 !important; }
[data-testid="stTable"] td { background-color: #2A2018 !important; color: #EEE0CC !important; border-color: #4A3828 !important; }
[data-testid="stTable"] tr:nth-child(even) td { background-color: #2E2418 !important; }

/* st.dataframe() outer wrapper */
[data-testid="stDataFrame"] { background-color: #2A2018 !important; border-color: #4A3828 !important; }
[data-testid="stDataFrame"] > div { background-color: #2A2018 !important; }

/* Form elements */
.stTextInput input,.stNumberInput input { background-color: #2A2018 !important; color: #EEE0CC !important; border-color: #4A3828 !important; }
.stTextArea textarea { background-color: #2A2018 !important; color: #EEE0CC !important; border-color: #4A3828 !important; }
[data-baseweb="input"] { background-color: #2A2018 !important; }
[data-baseweb="input"] input { color: #EEE0CC !important; }

/* Selectbox */
[data-baseweb="select"] > div { background-color: #2A2018 !important; color: #EEE0CC !important; border-color: #4A3828 !important; }
[data-baseweb="select"] span { color: #EEE0CC !important; }
[data-baseweb="popover"],[data-baseweb="menu"] { background-color: #2A2018 !important; }
li[role="option"],[data-baseweb="option"] { background-color: #2A2018 !important; color: #EEE0CC !important; }
li[role="option"]:hover,[data-baseweb="option"]:hover { background-color: #3A3020 !important; }

/* Labels */
[data-testid="stRadio"] label,[data-testid="stCheckbox"] label,[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label,[data-testid="stTextInput"] label,[data-testid="stNumberInput"] label,
[data-testid="stTextArea"] label,[data-testid="stFileUploader"] label { color: #EEE0CC !important; }

/* Buttons */
button[kind="secondary"] { background-color: #2A2018 !important; color: #EEE0CC !important; border-color: #4A3828 !important; }

/* Expanders */
[data-testid="stExpander"] { border-color: #4A3828 !important; }
details { background-color: #1C1510 !important; border-color: #4A3828 !important; }
details summary { background-color: #251C14 !important; color: #EEE0CC !important; }
details summary *,details summary p,details summary span,details summary div { color: #EEE0CC !important; fill: #EEE0CC !important; }
details summary svg,details summary svg path { fill: #EEE0CC !important; stroke: #EEE0CC !important; }
details > div,details > section { background-color: #1C1510 !important; }

/* Metrics */
[data-testid="stMetric"] { background-color: #2A2018 !important; border-radius: 8px; padding: 8px 12px !important; }
[data-testid="stMetricValue"] { color: #EEE0CC !important; }
[data-testid="stMetricLabel"] p { color: #C4956A !important; }
[data-testid="stMetricDelta"] { color: #8A6C4A !important; }

/* Captions & dividers */
[data-testid="stCaptionContainer"] p,.stCaption { color: #8A6C4A !important; }
hr,[data-testid="stDivider"] hr { border-color: #4A3828 !important; }

/* Alert boxes */
[data-testid="stAlertContentInfo"] { background-color: #1A2030 !important; }
[data-testid="stAlertContentSuccess"] { background-color: #122018 !important; }
[data-testid="stAlertContentWarning"] { background-color: #2A2010 !important; }
[data-testid="stAlertContentError"] { background-color: #2A1010 !important; }
[data-testid="stAlertContentInfo"] p,[data-testid="stAlertContentInfo"] span { color: #90CAF9 !important; }
[data-testid="stAlertContentSuccess"] p,[data-testid="stAlertContentSuccess"] span { color: #A5D6A7 !important; }
[data-testid="stAlertContentWarning"] p,[data-testid="stAlertContentWarning"] span { color: #FFCC80 !important; }
[data-testid="stAlertContentError"] p,[data-testid="stAlertContentError"] span { color: #EF9A9A !important; }
[data-testid="stInfo"] { background-color: #1A2030 !important; }
[data-testid="stSuccess"] { background-color: #122018 !important; }
[data-testid="stWarning"] { background-color: #2A2010 !important; }
[data-testid="stError"] { background-color: #2A1010 !important; }

/* File uploader */
[data-testid="stFileUploaderDropzone"] { background-color: #2A2018 !important; border-color: #4A3828 !important; }
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzoneInstructions"] * { color: #EEE0CC !important; }
[data-testid="stFileUploader"] small { color: #8A6C4A !important; }

/* Score pills — dark variants */
.score-good { background: #1a4029 !important; color: #86efac !important; }
.score-warn { background: #3d2e00 !important; color: #fde68a !important; }
.score-bad  { background: #3d0f17 !important; color: #fca5a5 !important; }

/* Family badge pills — dark variants */
.badge-retrieval  { background: #1e3a5f !important; color: #93c5fd !important; }
.badge-grounding  { background: #3b2800 !important; color: #fcd34d !important; }
.badge-generation { background: #2d1f5e !important; color: #c4b5fd !important; }
.badge-abstention { background: #3d0f1a !important; color: #fca5a5 !important; }
.badge-healthy    { background: #14402b !important; color: #86efac !important; }

/* Misc */
[data-baseweb="tag"] { background-color: #4A3828 !important; color: #EEE0CC !important; }
[data-testid="stStatusWidget"] { background-color: #2A2018 !important; }
[data-testid="stSpinner"] p { color: #EEE0CC !important; }
"""
    if _dark
    else ""
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
:root {{
{_css_vars}
}}

{_dark_overrides}

.block-container {{ padding-top: 1rem; padding-bottom: 2rem; }}

[data-testid="stCaptionContainer"],
.stCaption {{ color: var(--text-secondary) !important; }}

[data-testid="stMetricValue"] {{ font-weight: 700; }}

hr {{ border-color: var(--border) !important; }}

/* ── Hero ── */
.hero-title {{
    font-size: 2.7rem; font-weight: 800; letter-spacing: -0.5px;
    color: var(--text-h); margin: 0;
}}
.hero-sub {{ font-size: 1rem; color: var(--text-secondary); margin-top: 6px; }}

/* ── Feature ticker ── */
.ticker-outer {{
    overflow: hidden; background: var(--bg-ticker);
    border-radius: 999px; padding: 7px 0; margin: 12px 0 4px;
}}
.ticker-inner {{
    display: inline-block; white-space: nowrap;
    animation: scroll-left 42s linear infinite;
    font-size: 0.82rem; font-weight: 500; color: var(--ticker-text);
}}
@keyframes scroll-left {{
    0%   {{ transform: translateX(100vw); }}
    100% {{ transform: translateX(-100%); }}
}}
.ticker-sep {{ color: var(--ticker-sep); margin: 0 18px; }}

/* ── Cards ── */
.card {{
    background: var(--bg-card); border-radius: 12px; padding: 16px 20px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07); margin-bottom: 10px;
}}
.card-muted {{ background: var(--bg-card-muted); }}

/* ── Repair card accent ── */
.repair-card {{
    background: var(--bg-repair-card); border-left: 4px solid var(--border-accent);
    border-radius: 0 12px 12px 0; padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin: 10px 0;
}}

/* ── Family badge pills ── */
.badge {{
    display: inline-block; padding: 3px 12px; border-radius: 999px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
}}
.badge-retrieval  {{ background:#DBEAFE; color:#1E40AF; }}
.badge-grounding  {{ background:#FEF3C7; color:#92400E; }}
.badge-generation {{ background:#EDE9FE; color:#5B21B6; }}
.badge-abstention {{ background:#FFE4E6; color:#9F1239; }}
.badge-healthy    {{ background:#DCFCE7; color:#14532D; }}

/* ── Score pills ── */
.score-pill {{
    display: inline-block; padding: 2px 9px; border-radius: 999px;
    font-size: 0.78rem; font-weight: 600; margin: 2px 2px;
}}
.score-good {{ background:#DCFCE7; color:#166534; }}
.score-warn {{ background:#FEF9C3; color:#854D0E; }}
.score-bad  {{ background:#FFE4E6; color:#9F1239; }}

/* ── Param diff ── */
.param-current {{
    background:#FFE4E6; color:#9F1239; border-radius:6px; padding:5px 10px;
    text-align:center; font-family:monospace; font-size:0.9rem;
}}
.param-suggested {{
    background:#DCFCE7; color:#14532D; border-radius:6px; padding:5px 10px;
    text-align:center; font-family:monospace; font-size:0.9rem;
}}
.param-arrow {{ text-align:center; color:var(--arrow); font-size:1.2rem; padding-top:4px; }}

/* ── Family stat cards (benchmark) ── */
.fam-card {{ border-radius: 12px; padding: 18px 12px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}

/* ── Logo / pipeline ── */
.logo-wrap {{ text-align: center; padding: 2rem 1rem 0.4rem; user-select: none; }}
.logo-wordmark {{ font-size: 3rem; font-weight: 900; letter-spacing: -1px; color: var(--text-primary); margin: 0; line-height: 1; }}
.logo-tagline {{ font-size: 0.9rem; color: var(--text-secondary); letter-spacing: 0.18em; text-transform: uppercase; margin-top: 4px; font-weight: 500; }}
.pipe-stage {{ background: var(--bg-pipe-stage); color: var(--pipe-text); border-radius: 8px; padding: 5px 14px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; position: relative; }}
.pipe-stage-fail {{ background: #FEE2E2; color: #991B1B; border: 2px solid #FCA5A5; }}
.pipe-arrow {{ color: var(--arrow); font-size: 1rem; font-weight: 300; }}
.pipe-badge {{ position: absolute; top: -9px; right: -9px; background: #DC2626; color: white; border-radius: 50%; width: 18px; height: 18px; font-size: 9px; display: flex; align-items: center; justify-content: center; font-weight: 800; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }}
.pipe-fix {{ background: #DCFCE7; color: #166534; border: 2px solid #86EFAC; }}
.pipe-loop-label {{ font-size: 0.65rem; color: var(--text-secondary); text-align: center; margin-top: 2px; letter-spacing: 0.05em; }}

/* ── Docs section ── */
.doc-section {{ background: var(--bg-card); border-radius: 12px; padding: 20px 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin-bottom: 16px; }}
.doc-section h4 {{ color: var(--text-h4); margin-top: 0; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}

/* ── Score legend boxes (Metrics doc tab) ── */
.score-legend-good {{ background: var(--bg-gold); border-radius: 8px; padding: 10px; text-align: center; font-weight: 700; color: var(--text-h4); }}
.score-legend-warn {{ background: var(--bg-card-muted); border-radius: 8px; padding: 10px; text-align: center; font-weight: 700; color: var(--text-accent); }}
.score-legend-bad  {{ background: var(--bg-repair-card); border-radius: 8px; padding: 10px; text-align: center; font-weight: 700; color: var(--text-case); }}

/* ── Upload tab ── */
.upload-welcome {{ background: var(--bg-card); border-radius: 14px; padding: 22px 26px; border-left: 5px solid var(--border-accent); box-shadow: 0 1px 6px rgba(0,0,0,0.07); margin-bottom: 20px; }}
.upload-welcome h2 {{ margin: 0 0 6px; font-size: 1.25rem; color: var(--text-h); }}
.upload-welcome p  {{ margin: 0; font-size: 0.88rem; color: var(--text-secondary); line-height: 1.55; }}
.eval-file-card {{ background: var(--bg-card); border-radius: 12px; padding: 16px 18px; border: 1.5px solid var(--border); box-shadow: 0 1px 4px rgba(0,0,0,0.06); height: 100%; transition: border-color 0.15s; }}
.eval-file-card:hover {{ border-color: var(--border-accent); }}
.eval-file-card .efc-name {{ font-size: 0.85rem; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; word-break: break-all; }}
.eval-file-card .efc-stat {{ font-size: 0.78rem; color: var(--text-secondary); margin: 3px 0; }}
.eval-file-card .efc-stat b {{ color: var(--text-primary); }}
.section-label {{ font-size: 0.72rem; font-weight: 700; letter-spacing: 0.10em; text-transform: uppercase; color: var(--text-muted); margin: 18px 0 8px; }}
</style>
""", unsafe_allow_html=True)

# ── Documentation renderer (called when show_docs=True) ───────────────────────
def _render_docs():
    if st.button("← Back to App", key="docs_back"):
        st.session_state["show_docs"] = False
        st.rerun()

    st.markdown(
        '<div style="text-align:center;padding:1.2rem 0 0.4rem">'
        '<p style="font-size:2.2rem;font-weight:900;color:var(--text-primary);margin:0">📖 Rectify Documentation</p>'
        '<p style="font-size:0.88rem;color:var(--text-secondary);margin-top:5px">Complete reference for the RAG Repair Workbench</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    dt1, dt2, dt3, dt4, dt5, dt6 = st.tabs([
        "🏠 Overview", "🔄 Workflow", "🏷 Taxonomy", "📐 Metrics", "🔌 API", "⚖️ Comparison",
    ])

    with dt1:
        st.markdown("## What is Rectify?")
        st.markdown("""
Rectify is an **interactive post-evaluation workbench for RAG pipeline diagnosis, repair, and verification**.

It takes evaluation output from RAGVue, RAGAS, or any custom evaluator and guides developers
through: **failure clustering → root cause diagnosis → repair suggestions → human approval → sandbox rerun → before/after delta report.**
""")
        c1, c2, c3 = st.columns(3)
        for col, (icon, title, body) in zip([c1,c2,c3], [
            ("🔍", "Diagnose", "Clusters failures into 4 families and 23 fine-grained repair slices using metric-threshold heuristics. Fully deterministic and explainable."),
            ("🛠", "Repair", "Generates a parameterised repair card with an LLM-generated rationale. You review and approve before any change is applied."),
            ("✅", "Verify", "Reruns affected cases in a sandbox with the patched config, then shows a before/after delta report with per-case verdicts."),
        ]):
            col.markdown(
                f'<div style="background:var(--bg-card);border-radius:12px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">'
                f'<div style="font-size:1.8rem;text-align:center">{icon}</div>'
                f'<div style="font-weight:800;color:var(--text-primary);text-align:center;margin:8px 0 6px">{title}</div>'
                f'<div style="font-size:0.82rem;color:var(--text-secondary);line-height:1.5">{body}</div>'
                f'</div>', unsafe_allow_html=True,
            )
        st.divider()
        st.markdown("## Key Differentiators")
        st.markdown("""
- **Dataset-level clustering** — repairs affect whole failure slices, not individual cases
- **Developer-approved repairs** — every repair must be approved before it's applied
- **Verified delta** — sandbox reruns prove the repair actually improves metrics
- **Full provenance** — every approval/rejection logged to `repair_provenance.json`
- **No ML** — all clustering is rule-based: fast, interpretable, reproducible
""")

    with dt2:
        st.markdown("## Step-by-step Workflow")
        steps = [
            ("📄", "Generate RAG answers", "Run your RAG pipeline to produce answers for your question set.", "python -m rag.runner"),
            ("📊", "Evaluate with RAGVue", "Score every answer across 12 metrics (faithfulness, retrieval relevance, completeness, etc.).", "python evaluate.py"),
            ("📂", "Upload eval file", "Go to **Upload / Load** tab and upload the generated `eval_*.json` file, or select one from the pre-loaded eval files listed there.", None),
            ("🔍", "Diagnose", "Switch to **Diagnose** tab. Rectify clusters failures into families and slices, and infers root cause for each.", None),
            ("🛠", "Review repair card", "In **Repair Lab**, select a failure slice. A repair card shows: what to change, why, expected benefit, and trade-off.", None),
            ("✅", "Approve & sandbox", "Edit suggested parameter values if needed, click **✅ Approve**. Click **▶ Run Sandbox** to verify.", None),
            ("📋", "Check history", "All approvals/rejections are logged in **Approval History** tab or `repair_provenance.json`.", None),
        ]
        for i, (icon, title, body, cmd) in enumerate(steps, 1):
            with st.expander(f"Step {i}: {icon} {title}", expanded=(i <= 3)):
                st.markdown(body)
                if cmd:
                    st.code(cmd, language="bash")
        st.divider()
        st.markdown("## Demo Mode (no API key needed)")
        st.markdown("Go to **📂 Upload / Load** tab and select one of the included eval files (`eval_run_bm25.json`, `eval_run_dense.json`, `eval_run_hybrid.json`) to explore the full workflow without any setup.")

    with dt3:
        st.markdown("## 2-Layer Failure Taxonomy")
        st.markdown("### Layer 1: Failure Families")
        st.markdown("""
| Priority | Family | Icon | Trigger condition |
|---|---|---|---|
| 1 | Abstention | 🔴 | `negative_rejection < 0.5` |
| 2 | Retrieval | 🔵 | `retrieval_relevance < 0.45` OR `retrieval_coverage < 0.45` |
| 3 | Grounding | 🟡 | `strict_faithfulness < 0.5` |
| 4 | Generation | 🟣 | `clarity < 0.5` OR `coherence < 0.5` OR (`completeness < 0.4` AND `ret_rel ≥ 0.45`) |
""")
        st.divider()
        st.markdown("### Layer 2: Repair Slices (23 total)")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**🔵 Retrieval (R1–R7)**")
            st.markdown("R1 Partial coverage · R2 Noisy retrieval · R3 Evidence ignored · R4 Fragmented evidence · R5 Multi-part under-retrieval · R6 Distractor-dominated · R7 Sparse evidence")
            st.markdown("**🟡 Grounding (G1–G7)**")
            st.markdown("G1 Temporal misattribution · G2 Entity substitution · G3 Unsupported causal bridge · G4 Omitted qualifier · G5 Broken multi-hop · G6 Unsupported synthesis · G7 Citation drift")
        with col_r:
            st.markdown("**🟣 Generation — Synthesis (S1–S3)**")
            st.markdown("S1 Partial aspect coverage · S2 Shallow summarization · S3 Underused evidence")
            st.markdown("**🟣 Generation — Quality (Q1–Q3)**")
            st.markdown("Q1 Rambling · Q2 Poor structure · Q3 Internal inconsistency")
            st.markdown("**🔴 Abstention (A1–A3)**")
            st.markdown("A1 Confident unsupported · A2 Partial evidence overconfidence · A3 Ambiguous forced answer")

    with dt4:
        st.markdown("## Metric Reference")
        st.caption("All metrics scored 0–1 by the RAGVue judge (Mistral via local Ollama). No paid API used.")
        st.markdown("""
| Metric | What it measures | Failure threshold |
|---|---|---|
| `strict_faithfulness` | Claims supported by context? | < 0.5 |
| `answer_relevance` | Answer on-topic? | < 0.5 |
| `retrieval_relevance` | Retrieved chunks relevant? | < 0.45 |
| `answer_completeness` | All aspects covered? | < 0.4 |
| `context_utilization` | Context actually used? | < 0.35 |
| `coherence` | Internally consistent? | < 0.5 |
| `clarity` | Clearly written? | < 0.5 |
| `negative_rejection` | Abstains when evidence is insufficient? | < 0.5 |
| `retrieval_coverage` | Fraction of aspects in retrieved chunks? | < 0.45 |
| `multi_hop_faithfulness` | Multi-hop chains supported? | < 0.4 |
| `implicit_contradiction` | Hidden contradictions present? | < 0.4 |
| `answer_conciseness` | Not rambling? | < 0.5 |
""")
        sc1, sc2, sc3 = st.columns(3)
        sc1.markdown('<div class="score-legend-good">🟢 Good ≥ 0.7</div>', unsafe_allow_html=True)
        sc2.markdown('<div class="score-legend-warn">🟡 Warn 0.5–0.7</div>', unsafe_allow_html=True)
        sc3.markdown('<div class="score-legend-bad">🔴 Bad &lt; 0.5</div>', unsafe_allow_html=True)

    with dt5:
        st.markdown("## Capture API")
        st.code("""from Rectify import RAGCapture

capture = RAGCapture()

@capture.trace
def my_rag(question: str) -> str:
    contexts = retriever.retrieve(question)
    return generator.generate(question, contexts)

for q in questions:
    my_rag(q)

capture.export("results.jsonl")
""", language="python")
        st.divider()
        st.markdown("## Sandbox Backends")
        st.code("""from repair.sandbox_runner import run_sandbox

# RAGVue (default) — local Ollama/Mistral
results = run_sandbox(cases, patched_config, backend="ragvue")

# RAGAS
results = run_sandbox(cases, patched_config, backend="ragas")

# Custom evaluator
def my_eval(items): ...  # must add "ragvue_scores" key
results = run_sandbox(cases, patched_config, backend="custom",
                      custom_evaluate=my_eval)
""", language="python")

    with dt6:
        st.markdown("## Rectify vs. Related Tools")
        st.markdown("""
| Feature | **Rectify** | RAGXplain | Doctor-RAG | RAGAS |
|---|---|---|---|---|
| Scope | ✅ Dataset-level | ❌ Per-item | ❌ Per-item | ❌ Per-item |
| Failure clustering | ✅ 4 families × 23 slices | ❌ | ❌ | ❌ |
| Developer approval gate | ✅ | ❌ | ❌ | ❌ |
| Sandbox delta verification | ✅ | ❌ | ❌ | ❌ |
| Full provenance audit log | ✅ | ❌ | ❌ | ❌ |
| Works without paid API | ✅ Ollama/Mistral | ❌ | ❌ | Partial |
""")
        st.divider()
        st.markdown("## Novelty Statement")
        st.info("""
**Dataset-level** — Rectify clusters failures across the whole eval set and proposes one repair per slice.
RAGXplain and Doctor-RAG diagnose individual items in isolation, missing systemic patterns.

**Verified** — Before any repair is committed, Rectify reruns affected cases in a sandbox and computes a
before/after delta. Doctor-RAG proposes fixes with no empirical validation.
""")


# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;padding:2rem 0 0.3rem">'
    '<p style="font-size:4rem;font-weight:900;letter-spacing:-2px;color:var(--text-primary);margin:0;line-height:1;">🔧 RECTIFY</p>'
    '<p style="font-size:0.95rem;color:var(--text-secondary);letter-spacing:0.15em;text-transform:uppercase;font-weight:500;margin-top:6px;">'
    'Interactive Post-Evaluation Workbench</p>'
    '<p style="font-size:1.1rem;color:var(--text-primary);font-weight:600;margin-top:14px;">'
    'Stop debugging RAG case-by-case. Cluster the failures, approve one fix, verify the delta.'
    '</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Pipeline diagram — 100% native Streamlit, no HTML layout ──────────────────
st.write("")  # spacer

def _stage_card(col, icon, label, bg, fg, desc, fail=False):
    border = f"border:2px solid #FCA5A5;" if fail else ""
    col.markdown(
        f'<div style="background:{bg};{border}border-radius:8px;padding:6px 4px;'
        f'text-align:center;">'
        f'<div style="font-size:1rem">{icon}</div>'
        f'<div style="font-size:0.58rem;font-weight:800;color:{fg};margin-top:2px;'
        f'letter-spacing:0.04em">{label}</div>'
        f'</div>'
        f'<div style="font-size:0.54rem;color:var(--pipe-desc);text-align:center;margin-top:3px;line-height:1.3">{desc}</div>',
        unsafe_allow_html=True,
    )

def _arrow(col, fg="var(--arrow)"):
    col.markdown(
        f'<div style="text-align:center;font-size:1rem;color:{fg};padding-top:10px">→</div>',
        unsafe_allow_html=True,
    )

# Label row: "🔧 RECTIFY" floated above last 3 stage columns
# Widths match the stage row below: 4 stages + 3 arrows (left half) vs 3 stages + 2 arrows (right)
# Left half total weight = 4*2 + 3*.3 = 8.9  |  Right = 3*2 + 2*.3 = 6.6  |  separator arrow = .3
_lbl_left, _lbl_sep, _lbl_right = st.columns([8.9, .3, 6.6])
_lbl_right.markdown(
    '<div style="text-align:center;font-size:0.62rem;font-weight:900;color:var(--text-accent);'
    'letter-spacing:0.12em;border:1.5px dashed var(--border-answer);border-bottom:none;'
    'border-radius:6px 6px 0 0;padding:3px 0;margin-bottom:0;background:var(--bg-label)">'
    '🔧 RECTIFY</div>',
    unsafe_allow_html=True,
)

# Single row: all 7 stages + 6 arrows
c1,a1,c2,a2,c3,a3,c4,a4,d1,da,d2,db,d3 = st.columns([2,.3,2,.3,2,.3,2,.3,2,.3,2,.3,2])
_stage_card(c1, "📄",  "QUERY",    "var(--bg-pipe-stage)", "var(--pipe-text)", "User question")
_arrow(a1)
_stage_card(c2, "🔎",  "RETRIEVE", "var(--bg-pipe-stage)", "var(--pipe-text)", "Top-k chunks")
_arrow(a2)
_stage_card(c3, "⚡", "GENERATE", "var(--bg-pipe-stage)", "var(--pipe-text)", "Answer", fail=False)
_arrow(a3)
_stage_card(c4, "📊",  "EVALUATE", "var(--bg-pipe-stage)", "var(--pipe-text)", "12 metrics")
_arrow(a4, fg="var(--text-accent)")
_stage_card(d1, "🔍",  "DIAGNOSE", "#FEF3C7", "#92400E", "4 families · 23 slices")
_arrow(da, fg="var(--text-accent)")
_stage_card(d2, "🛠",  "REPAIR",   "#EDE9FE", "#5B21B6", "Human approves")
_arrow(db, fg="var(--text-accent)")
_stage_card(d3, "✅",  "VERIFY",   "#DCFCE7", "#166534", "Sandbox delta")


# ── Feature ticker ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="ticker-outer">
  <span class="ticker-inner">
    ✦ Dataset-level failure clustering across 4 failure families
    <span class="ticker-sep">|</span>
    🔍 Rule-based root cause inference per repair slice
    <span class="ticker-sep">|</span>
    🛠 23 fine-grained repair slices (R1–R7 · G1–G7 · S1–S3 · Q1–Q3 · A1–A3)
    <span class="ticker-sep">|</span>
    ✅ Developer approval gate before any change is applied
    <span class="ticker-sep">|</span>
     📊 Before / after metric delta report with per-case verdicts
    <span class="ticker-sep">|</span>
    📜 Full repair provenance audit log
    <span class="ticker-sep">|</span>
    🤖 Compound failure detection across co-firing families
  </span>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Theme toggle ──
    _t_col, _t_lbl = st.columns([1, 3])
    with _t_col:
        if st.button("☀️" if _dark else "🌙", key="theme_toggle", help="Toggle dark/light mode"):
            st.session_state["dark_mode"] = not _dark
            st.rerun()
    with _t_lbl:
        st.caption("Light mode" if _dark else "Dark mode")

    st.markdown(
        '<div style="text-align:center;padding:0.8rem 0 0.4rem">'
        '<span style="font-size:1.6rem;font-weight:900;color:var(--text-primary);letter-spacing:-1px">🔧 RECTIFY</span><br>'
        '<span style="font-size:0.7rem;color:var(--text-secondary);letter-spacing:0.1em;text-transform:uppercase">RAG Repair Workbench</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    from pathlib import Path
    import json

    eval_dir = Path("evals")
    existing = sorted(eval_dir.glob("eval_*.json")) if eval_dir.exists() else []

    # ── Dataset status ──
    st.markdown("**📁 Datasets**")
    if existing:
        for p in existing:
            try:
                data  = json.loads(p.read_text())
                n     = len(data.get("results", []))
                summ  = data.get("summary", {})
                faith = summ.get("strict_faithfulness", None)
                st.markdown(
                    f'<div style="background:var(--bg-sidebar-card);border-radius:8px;padding:8px 10px;margin-bottom:6px">'
                    f'<div style="font-size:0.75rem;font-weight:700;color:var(--text-primary)">{p.stem}</div>'
                    f'<div style="font-size:0.68rem;color:var(--text-secondary)">{n} cases'
                    f'{f" · faith {faith:.2f}" if isinstance(faith, float) else ""}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
            except Exception:
                st.markdown(f"- `{p.stem}`")
    else:
        st.markdown(
            '<div style="background:var(--bg-sidebar-card);border-radius:8px;padding:8px 10px;'
            'font-size:0.75rem;color:var(--text-secondary)">No eval files yet.<br>'
            'Run <code>python evaluate.py</code></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Workflow guide ──
    st.markdown("**🗺 Workflow**")
    _STEPS = [
        ("📂", "Upload",   "Add a RAGVue eval file"),
        ("🔍", "Diagnose", "Cluster failures into families & slices"),
        ("🛠", "Repair",   "Approve a parameterised fix"),
        ("▶",  "Sandbox",  "Rerun affected cases with patch"),
        ("📊", "Verify",   "Review before/after delta report"),
    ]
    for i, (icon, step, detail) in enumerate(_STEPS, 1):
        st.markdown(
            f'<div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:7px">'
            f'<div style="background:var(--bg-step-num);border-radius:50%;width:22px;height:22px;'
            f'flex-shrink:0;display:flex;align-items:center;justify-content:center;'
            f'font-size:0.7rem;font-weight:800;color:var(--pipe-text)">{i}</div>'
            f'<div><div style="font-size:0.75rem;font-weight:700;color:var(--text-primary)">{icon} {step}</div>'
            f'<div style="font-size:0.65rem;color:var(--text-secondary);line-height:1.3">{detail}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Failure families legend ──
    st.markdown("**🏷 Failure families**")
    _FAM_LEGEND = [
        ("#DBEAFE", "#1E40AF", "🔵 Retrieval",  "Bad chunks / low coverage"),
        ("#FEF3C7", "#92400E", "🟡 Grounding",  "Hallucination / drift"),
        ("#EDE9FE", "#5B21B6", "🟣 Generation", "Clarity / coherence"),
        ("#FFE4E6", "#9F1239", "🔴 Abstention", "Confident unsupported answers"),
    ]
    for bg, fg, name, hint in _FAM_LEGEND:
        st.markdown(
            f'<div style="background:{bg};border-radius:7px;padding:5px 9px;margin-bottom:5px">'
            f'<div style="font-size:0.72rem;font-weight:700;color:{fg}">{name}</div>'
            f'<div style="font-size:0.63rem;color:{fg};opacity:.8">{hint}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("**📖 Documentation**")
    if st.button("📖 Open full documentation →", use_container_width=True, key="open_docs"):
        st.session_state["show_docs"] = True
    st.caption("Workflow · taxonomy · metrics · API · comparison")

    st.divider()
    st.markdown(
        '<div style="font-size:0.65rem;color:var(--text-muted);text-align:center">'
        'Built with RAGVue · Streamlit</div>',
        unsafe_allow_html=True,
    )

# ── Session state init ────────────────────────────────────────────────────────
for key, default in [("repair_slice_idx", 0), ("repair_eval_file", None), ("active_eval_file", None), ("show_docs", False)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Documentation full-page view ──────────────────────────────────────────────
if st.session_state.get("show_docs"):
    _render_docs()
    st.stop()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_upload, tab_explorer, tab_diagnose, tab_repair, tab_delta, tab_history = st.tabs([
    "📂  Upload / Load",
    "🔎  Case Explorer",
    "🔍  Diagnose",
    "🛠  Repair Lab",
    "📈  Delta Explorer",
    "📋  Approval History",
])

# ── Upload / Load ──────────────────────────────────────────────────────────────
with tab_upload:
    existing = sorted(eval_dir.glob("eval_*.json")) if eval_dir.exists() else []

    st.markdown(
        '<div class="upload-welcome">'
        '<h2>👋 Welcome to Rectify</h2>'
        '<p>Load a RAGVue evaluation file to start diagnosing your RAG pipeline. '
        'Rectify clusters failures into <strong>4 families · 23 repair slices</strong>, '
        'generates parameterised repair cards for human approval, and runs a before/after '
        'sandbox verification — all in one workbench.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    import os as _os
    _teaser_path = "paper_figures/Teaser_figure.png"
    if _os.path.exists(_teaser_path):
        with st.expander("📊 See how Rectify reduces debugging effort", expanded=False):
            _tl, _tc, _tr = st.columns([1, 3, 1])
            with _tc:
                st.image(
                    _teaser_path,
                    # caption="Rectify reduces developer decisions by 97% — from 74–89 case inspections to 2–3 repair cards.",
                    use_container_width=True,
                )

    if existing:
        st.markdown('<div class="section-label">📁 Available eval files</div>', unsafe_allow_html=True)
        rows = [existing[i:i+3] for i in range(0, len(existing), 3)]
        for row in rows:
            cols = st.columns(3)
            for col, p in zip(cols, row):
                try:
                    data    = json.loads(p.read_text())
                    n       = len(data.get("results", []))
                    summ    = data.get("summary", {})
                    faith   = summ.get("strict_faithfulness", None)
                    ret_rel = summ.get("retrieval_relevance", None)
                    active  = st.session_state.get("active_eval_file") == p
                    border  = "border-color: var(--border-accent);" if active else ""
                    faith_s = f"<b>{faith:.2f}</b>" if isinstance(faith, float) else "—"
                    ret_s   = f"<b>{ret_rel:.2f}</b>" if isinstance(ret_rel, float) else "—"
                    col.markdown(
                        f'<div class="eval-file-card" style="{border}">'
                        f'<div class="efc-name">📄 {p.name}</div>'
                        f'<div class="efc-stat">Cases &nbsp;<b>{n}</b></div>'
                        f'<div class="efc-stat">Faithfulness &nbsp;{faith_s}</div>'
                        f'<div class="efc-stat">Retrieval rel. &nbsp;{ret_s}</div>'
                        f'</div>', unsafe_allow_html=True,
                    )
                    if col.button("✓ Loaded" if active else "Load →",
                                  key=f"load_{p.stem}",
                                  type="primary" if not active else "secondary",
                                  use_container_width=True):
                        st.session_state["active_eval_file"] = p
                        st.rerun()
                except Exception:
                    col.markdown(f"`{p.name}`")

        if st.session_state.get("active_eval_file"):
            af = st.session_state["active_eval_file"]
            st.success(f"**`{af.name}`** is active — open **🔍 Diagnose** or **🛠 Repair Lab** to continue.", icon="✅")
    else:
        st.info("No eval files found in `evals/`. Run `python evaluate.py` first.", icon="📭")

    st.markdown('<div class="section-label">⬆ Upload a RAGVue eval file</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Drop a RAGVue JSON file here", type=["json"], key="upload_ragvue",
                                help="Export from RAGVue using `ragvue.export('results.json')`")
    if uploaded:
        eval_dir.mkdir(exist_ok=True)
        dest = eval_dir / uploaded.name
        dest.write_bytes(uploaded.read())
        st.session_state["active_eval_file"] = dest
        st.success(f"Saved to `{dest}` and set as active file.", icon="✅")
        st.rerun()

# ── Case Explorer ─────────────────────────────────────────────────────────────
with tab_explorer:
    st.markdown("## 🔎 Case Explorer")
    st.caption("Inspect every case: query · retrieved contexts · generated answer · gold answer · scores · retriever")

    from repair.loader import load_eval_results
    from repair.clustering import slice_cases as _slice_cases

    _exp_files = sorted(eval_dir.glob("eval_*.json")) if eval_dir.exists() else []
    if not _exp_files:
        st.warning("No eval files found. Go to **📂 Upload / Load** first.")
    else:
        _exp_active = st.session_state.get("active_eval_file")
        _exp_default = _exp_files.index(_exp_active) if _exp_active in _exp_files else 0
        _exp_path = st.selectbox("Eval file", _exp_files, index=_exp_default,
                                 format_func=lambda p: p.name, key="explorer_sel")
        _exp_cases   = load_eval_results(_exp_path)
        _exp_sliced  = _slice_cases(_exp_cases)
        _sc_by_id    = {sc.case.case_id: sc for sc in _exp_sliced}

        # Load raw JSON for config/settings
        _raw_results = {
            r.get("case_id") or f"{r.get('question_id','q')}_{r.get('retriever', str(i))}": r
            for i, r in enumerate(json.loads(_exp_path.read_text()).get("results", []))
        }

        # Filters
        fc1, fc2, fc3 = st.columns(3)
        _families     = ["all"] + sorted({sc.family.value for sc in _exp_sliced})
        _retrievers   = ["all"] + sorted({c.retriever for c in _exp_cases if c.retriever})
        _fam_filter   = fc1.selectbox("Family",   _families,   key="exp_fam")
        _ret_filter   = fc2.selectbox("Retriever", _retrievers, key="exp_ret")
        _verdict_filter = fc3.selectbox("Verdict", ["all", "healthy", "failure"], key="exp_verdict")

        _filtered = [
            sc for sc in _exp_sliced
            if (_fam_filter   == "all" or sc.family.value == _fam_filter)
            and (_ret_filter  == "all" or sc.case.retriever == _ret_filter)
            and (_verdict_filter == "all"
                 or (_verdict_filter == "healthy"  and sc.family.value == "none")
                 or (_verdict_filter == "failure"  and sc.family.value != "none"))
        ]

        st.caption(f"Showing **{len(_filtered)}** of {len(_exp_sliced)} cases")

        # Summary table
        import pandas as pd
        _tbl_rows = []
        for sc in _filtered:
            s = sc.case.scores
            _tbl_rows.append({
                "Case ID":    sc.case.case_id,
                "Retriever":  sc.case.retriever or "—",
                "Family":     sc.family.value,
                "Slice":      sc.slice_label,
                "Faith":      f"{s.strict_faithfulness:.2f}",
                "Ret Rel":    f"{s.retrieval_relevance:.2f}",
                "Complete":   f"{s.answer_completeness:.2f}",
                "Coherence":  f"{s.coherence:.2f}",
            })
        st.dataframe(pd.DataFrame(_tbl_rows), use_container_width=True, hide_index=True, height=380)

        # ── Compound failure table ─────────────────────────────────────────
        _compound = [sc for sc in _filtered if sc.secondary_family and sc.secondary_family.value != "none"]
        if _compound:
            st.divider()
            st.markdown(f"### ⚠️ Compound failures ({len(_compound)})")
            st.caption("Cases where two failure families co-fire — these need a combined repair.")

            _BADGE_MAP = {
                "retrieval": "badge-retrieval", "grounding": "badge-grounding",
                "generation": "badge-generation", "abstention": "badge-abstention",
            }

            for _csc in _compound:
                _cc = _csc.case
                _cs = _cc.scores
                _pri_cls = _BADGE_MAP.get(_csc.family.value, "")
                _sec_cls = _BADGE_MAP.get(_csc.secondary_family.value, "")
                with st.expander(
                    f"⚠️  {_cc.case_id}  ·  {_csc.family.value} + {_csc.secondary_family.value}  ·  {_csc.slice_label}",
                    expanded=False,
                ):
                    # Family badges + slice
                    st.markdown(
                        f'<span class="badge {_pri_cls}">{_csc.family.value}</span>'
                        f'<span style="margin:0 6px;color:var(--text-muted)">+</span>'
                        f'<span class="badge {_sec_cls}">{_csc.secondary_family.value}</span>'
                        f'<span style="margin-left:10px;font-size:0.82rem;color:var(--text-secondary)">{_csc.slice_label}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Query:** {_cc.question}")

                    # Score pills
                    _cpills = " ".join(
                        f'<span class="score-pill {"score-good" if v >= 0.7 else ("score-warn" if v >= 0.5 else "score-bad")}">'
                        f'{k}: {v:.2f}</span>'
                        for k, v in {
                            "faith": _cs.strict_faithfulness,
                            "ret_rel": _cs.retrieval_relevance,
                            "complete": _cs.answer_completeness,
                            "coherence": _cs.coherence,
                            "clarity": _cs.clarity,
                        }.items()
                    )
                    st.markdown(_cpills, unsafe_allow_html=True)
                    st.write("")

                    # Contexts
                    if _cc.contexts:
                        with st.expander(f"📄 Retrieved contexts ({len(_cc.contexts)})", expanded=False):
                            for _ci, _ctx in enumerate(_cc.contexts, 1):
                                st.markdown(
                                    f'<div style="background:var(--bg-card);border-left:3px solid var(--border-answer);'
                                    f'padding:8px 12px;border-radius:0 8px 8px 0;margin-bottom:6px;font-size:0.84rem">'
                                    f'<b>Chunk {_ci}</b><br>{_ctx}</div>',
                                    unsafe_allow_html=True,
                                )

                    # Answers side by side
                    _ca1, _ca2 = st.columns(2)
                    with _ca1:
                        st.markdown("**Generated answer**")
                        st.markdown(
                            f'<div style="background:var(--bg-answer);border-left:3px solid var(--border-answer);'
                            f'padding:10px 14px;border-radius:0 8px 8px 0;font-size:0.87rem;line-height:1.5;color:var(--text-primary)">'
                            f'{_cc.answer or "<em>no answer</em>"}</div>',
                            unsafe_allow_html=True,
                        )
                    with _ca2:
                        st.markdown("**Gold answer**")
                        st.markdown(
                            f'<div style="background:var(--bg-gold);border-left:3px solid #86EFAC;'
                            f'padding:10px 14px;border-radius:0 8px 8px 0;font-size:0.87rem;line-height:1.5;color:var(--text-primary)">'
                            f'{_cc.expected_answer or "<em>no gold answer</em>"}</div>',
                            unsafe_allow_html=True,
                        )

                    # Gold evidence
                    _craw = _raw_results.get(_cc.case_id, {})
                    _rel_docs = _craw.get("relevant_doc_ids", [])
                    if _rel_docs:
                        _doc_tags = " ".join(
                            f'<span style="background:var(--bg-gold);border:1px solid #86EFAC;'
                            f'border-radius:4px;padding:2px 8px;font-size:0.78rem;margin-right:4px">'
                            f'{d}</span>'
                            for d in _rel_docs
                        )
                        st.markdown(f"**Gold evidence (relevant docs):** {_doc_tags}", unsafe_allow_html=True)

                    # Diagnosis signals
                    if _csc.matched_signals:
                        st.markdown("**Diagnosis signals:**")
                        for _sig in _csc.matched_signals:
                            st.markdown(f"- `{_sig}`")

        st.divider()
        st.markdown("### Case detail")

        _case_ids   = [sc.case.case_id for sc in _filtered]
        _sel_case_id = st.selectbox("Select case", _case_ids, key="exp_case_sel")
        _sel_sc      = next((sc for sc in _filtered if sc.case.case_id == _sel_case_id), None)

        if _sel_sc:
            c = _sel_sc.case
            s = c.scores
            raw = _raw_results.get(c.case_id, {})
            _BADGE_EXP = {
                "retrieval": ("badge-retrieval", "🔵"), "grounding": ("badge-grounding", "🟡"),
                "generation": ("badge-generation", "🟣"), "abstention": ("badge-abstention", "🔴"),
                "none": ("badge-healthy", "🟢"),
            }
            badge_cls, fam_icon = _BADGE_EXP.get(_sel_sc.family.value, ("", "●"))

            # Header row
            hc1, hc2, hc3 = st.columns([3, 1, 1])
            hc1.markdown(f"**{c.case_id}**  ·  retriever: `{c.retriever or '—'}`")
            hc2.markdown(f'<span class="badge {badge_cls}">{fam_icon} {_sel_sc.family.value}</span>',
                         unsafe_allow_html=True)
            hc3.markdown(f"*{_sel_sc.slice_label}*")

            # Query
            st.markdown(f"**Query:** {c.question}")

            # Scores pills
            _score_map = {
                "faithfulness": s.strict_faithfulness, "ret_rel": s.retrieval_relevance,
                "completeness": s.answer_completeness, "coherence": s.coherence,
                "clarity": s.clarity, "conciseness": s.answer_conciseness,
            }
            pills_html = " ".join(
                f'<span class="score-pill {"score-good" if v and v >= 0.7 else ("score-warn" if v and v >= 0.5 else "score-bad")}">'
                f'{k}: {v:.2f}</span>'
                for k, v in _score_map.items() if v is not None
            )
            st.markdown(pills_html, unsafe_allow_html=True)

            st.divider()

            # Contexts
            with st.expander(f"📄 Retrieved contexts ({len(c.contexts)})", expanded=False):
                for ci, ctx in enumerate(c.contexts, 1):
                    st.markdown(
                        f'<div style="background:var(--bg-card);border-left:3px solid var(--border-answer);'
                        f'padding:8px 12px;border-radius:0 8px 8px 0;margin-bottom:6px;font-size:0.85rem">'
                        f'<b>Chunk {ci}</b><br>{ctx}</div>',
                        unsafe_allow_html=True,
                    )

            # Answers side by side
            ga1, ga2 = st.columns(2)
            with ga1:
                st.markdown("**Generated answer**")
                st.markdown(
                    f'<div style="background:var(--bg-answer);border-left:3px solid var(--border-answer);'
                    f'padding:10px 14px;border-radius:0 8px 8px 0;font-size:0.88rem;line-height:1.5;color:var(--text-primary)">'
                    f'{c.answer or "<em>no answer</em>"}</div>',
                    unsafe_allow_html=True,
                )
            with ga2:
                st.markdown("**Gold answer**")
                st.markdown(
                    f'<div style="background:var(--bg-gold);border-left:3px solid #86EFAC;'
                    f'padding:10px 14px;border-radius:0 8px 8px 0;font-size:0.88rem;line-height:1.5;color:var(--text-primary)">'
                    f'{c.expected_answer or "<em>no gold answer</em>"}</div>',
                    unsafe_allow_html=True,
                )

            # Gold evidence
            _rel_docs = raw.get("relevant_doc_ids", [])
            if _rel_docs:
                _doc_tags = " ".join(
                    f'<span style="background:var(--bg-gold);border:1px solid #86EFAC;'
                    f'border-radius:4px;padding:2px 8px;font-size:0.78rem;margin-right:4px">'
                    f'{d}</span>'
                    for d in _rel_docs
                )
                st.markdown(f"**Gold evidence (relevant docs):** {_doc_tags}", unsafe_allow_html=True)

            # Config / settings used
            cfg = raw.get("config", {})
            if cfg:
                st.markdown("**Pipeline settings used:**")
                cfg_cols = st.columns(len(cfg))
                for col, (k, v) in zip(cfg_cols, cfg.items()):
                    col.metric(k.replace("_", " "), str(v))

            # Diagnosis signals
            if _sel_sc.matched_signals:
                st.markdown("**Diagnosis signals:**")
                for sig in _sel_sc.matched_signals:
                    st.markdown(f"- `{sig}`")

# ── Delta Explorer ─────────────────────────────────────────────────────────────
with tab_delta:
    st.markdown("## 📈 Delta Explorer")
    st.caption("Before / after metric deltas for every sandbox run — persisted across sessions")

    _delta_dir = Path("evals/deltas")
    _delta_files = sorted(_delta_dir.glob("*.json")) if _delta_dir.exists() else []

    if not _delta_files:
        st.info("No sandbox runs recorded yet. Run a sandbox in **🛠 Repair Lab** first.")
    else:
        _delta_sel = st.selectbox(
            "Select sandbox run",
            _delta_files,
            format_func=lambda p: (lambda d: f"[{d.get('eval_file', '—')}]  {d.get('slice_label', p.stem)}")(json.loads(p.read_text())),
            key="delta_sel",
        )
        _dr = json.loads(_delta_sel.read_text())
        summ = _dr.get("summary", {})

        _dh1, _dh2 = st.columns([6, 1])
        _dh1.markdown(f"### {_dr.get('slice_label','—')}  ·  `{_dr.get('family','—')}`")
        _dh1.caption(f"Run at {_dr.get('ran_at','—')[:19].replace('T',' ')}")
        if _dh2.button("🗑 Delete", key=f"del_delta_{_delta_sel.stem}", type="secondary", use_container_width=True):
            _delta_sel.unlink()
            st.success("Delta run deleted.")
            st.rerun()

        # Summary metrics
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Improved",         summ.get("improved", 0),
                   delta=f"+{summ.get('improved',0)}", delta_color="normal")
        mc2.metric("Unchanged",        summ.get("unchanged", 0))
        mc3.metric("Regressed",        summ.get("regressed", 0),
                   delta=f"-{summ.get('regressed',0)}", delta_color="inverse")
        mc4.metric("Improvement rate", f"{summ.get('improvement_rate',0):.0%}")

        # Before / after chart
        import pandas as pd
        avg_d = summ.get("avg_deltas", {})
        before_avg = summ.get("before_avg", {})
        after_avg  = summ.get("after_avg", {})
        if avg_d:
            delta_df = pd.DataFrame({
                "metric": list(avg_d.keys()),
                "before": [before_avg.get(m, 0) for m in avg_d],
                "after":  [after_avg.get(m, 0)  for m in avg_d],
                "Δ":      list(avg_d.values()),
            })
            dc1, dc2 = st.columns([3, 2])
            with dc1:
                st.markdown("**Before vs After (avg)**")
                st.bar_chart(delta_df.set_index("metric")[["before", "after"]], height=260)
            with dc2:
                st.markdown("**Score deltas**")
                disp = delta_df.copy()
                disp["before"] = disp["before"].map("{:.2f}".format)
                disp["after"]  = disp["after"].map("{:.2f}".format)
                disp["Δ"]      = disp["Δ"].map("{:+.3f}".format)
                st.table(disp.set_index("metric"))

        # Per-case breakdown
        st.divider()
        st.markdown("**Per-case results**")
        _V = {"improved": "✅", "unchanged": "➖", "regressed": "❌"}
        for case in _dr.get("cases", []):
            verdict = case.get("verdict", "—")
            icon = _V.get(verdict, "—")
            with st.expander(f"{icon}  {case['case_id']}  —  {verdict}", expanded=False):
                st.markdown(f"**Question:** {case.get('question','—')}")
                ca1, ca2 = st.columns(2)
                with ca1:
                    st.markdown("**Before answer**")
                    st.markdown(
                        f'<div style="background:var(--bg-answer);border-left:3px solid var(--border-answer);'
                        f'padding:10px 14px;border-radius:0 8px 8px 0;font-size:0.85rem;line-height:1.5;color:var(--text-primary)">'
                        f'{case.get("before_answer") or "<em>—</em>"}</div>',
                        unsafe_allow_html=True,
                    )
                with ca2:
                    st.markdown("**After answer**")
                    bc = "#86EFAC" if verdict == "improved" else ("#FCA5A5" if verdict == "regressed" else "var(--border-answer)")
                    after_bg = "var(--bg-gold)" if verdict == "improved" else ("var(--bg-answer)" if verdict == "regressed" else "var(--bg-answer)")
                    st.markdown(
                        f'<div style="background:{after_bg};border-left:3px solid {bc};'
                        f'padding:10px 14px;border-radius:0 8px 8px 0;font-size:0.85rem;line-height:1.5;color:var(--text-primary)">'
                        f'{case.get("after_answer") or "<em>—</em>"}</div>',
                        unsafe_allow_html=True,
                    )
                # Score delta table
                deltas = case.get("deltas", {})
                before_s = case.get("before_scores", {})
                after_s  = case.get("after_scores", {})
                if deltas:
                    rows = [{"metric": m,
                             "before": f"{before_s.get(m,0):.2f}",
                             "after":  f"{after_s.get(m,0):.2f}",
                             "Δ":      f"{v:+.3f}"} for m, v in deltas.items()]
                    st.table(pd.DataFrame(rows).set_index("metric"))
                # Retrieved contexts
                before_ctx = case.get("before_contexts", [])
                after_ctx  = case.get("after_contexts", [])
                if before_ctx or after_ctx:
                    with st.expander("Retrieved contexts", expanded=False):
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            st.markdown("**Before**")
                            for i, ctx in enumerate(before_ctx, 1):
                                st.markdown(
                                    f'<div style="background:var(--bg-answer);border-left:3px solid var(--border-answer);'
                                    f'padding:8px 12px;border-radius:0 6px 6px 0;font-size:0.80rem;'
                                    f'line-height:1.5;color:var(--text-primary);margin-bottom:6px">'
                                    f'<strong>#{i}</strong> {ctx}</div>',
                                    unsafe_allow_html=True,
                                )
                        with cc2:
                            st.markdown("**After**")
                            for i, ctx in enumerate(after_ctx, 1):
                                st.markdown(
                                    f'<div style="background:var(--bg-answer);border-left:3px solid #86EFAC;'
                                    f'padding:8px 12px;border-radius:0 6px 6px 0;font-size:0.80rem;'
                                    f'line-height:1.5;color:var(--text-primary);margin-bottom:6px">'
                                    f'<strong>#{i}</strong> {ctx}</div>',
                                    unsafe_allow_html=True,
                                )

# ── Diagnose ───────────────────────────────────────────────────────────────────
with tab_diagnose:
    st.markdown("## 🔍 Failure Diagnosis")

    from pathlib import Path as _Path
    from repair.loader import load_eval_results
    from repair.clustering import slice_cases, build_slices
    from repair.models import RepairSlice, FailureFamily
    from repair.root_cause import infer_root_cause

    eval_files = sorted(_Path("evals").glob("eval_*.json")) if _Path("evals").exists() else []
    if not eval_files:
        st.warning("No eval files in `evals/`. Go to **📂 Upload / Load** first.")
    else:
        active = st.session_state.get("active_eval_file")
        default_idx = eval_files.index(active) if active in eval_files else 0
        sel = st.selectbox(
            "Select eval file",
            eval_files,
            index=default_idx,
            format_func=lambda p: p.name,
            key="diagnose_sel",
        )

        cases = load_eval_results(sel)
        sliced = slice_cases(cases)
        slices = build_slices(sliced)

        failure    = [s for s in slices if s.slice_type != RepairSlice.none]
        healthy_n  = next((s.size for s in slices if s.slice_type == RepairSlice.none), 0)

        # Top stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total cases",    len(cases))
        c2.metric("Failure slices", len(failure))
        c3.metric("Failing cases",  sum(s.size for s in failure))
        c4.metric("Healthy cases",  healthy_n)

        # Family breakdown
        if failure:
            st.markdown("### Failures by family")
            _FAM_ICON = {
                "retrieval": "🔵", "grounding": "🟡",
                "generation": "🟣", "abstention": "🔴",
            }
            family_counts: dict[str, int] = {}
            for s in failure:
                family_counts[s.family.value] = family_counts.get(s.family.value, 0) + s.size
            cols = st.columns(len(family_counts))
            for col, (fam, count) in zip(cols, sorted(family_counts.items())):
                col.metric(f"{_FAM_ICON.get(fam,'●')} {fam.title()}", count)

        st.divider()
        st.markdown("### Failure slices")

        _BADGE_CLS = {
            "retrieval": "badge-retrieval", "grounding": "badge-grounding",
            "generation": "badge-generation", "abstention": "badge-abstention",
            "none": "badge-healthy",
        }

        def _pills(avg_scores: dict) -> str:
            out = []
            for m, v in avg_scores.items():
                cls = "score-good" if v >= 0.7 else ("score-warn" if v >= 0.5 else "score-bad")
                out.append(f'<span class="score-pill {cls}">{m.replace("_"," ")[:10]}: {v:.2f}</span>')
            return " ".join(out)

        for s in slices:
            is_healthy = s.slice_type == RepairSlice.none
            icon = "🟢" if is_healthy else "🔴"
            badge = _BADGE_CLS.get(s.family.value, "")
            with st.expander(
                f"{icon}  {s.slice_label}  —  {s.size} case{'s' if s.size != 1 else ''}",
                expanded=(not is_healthy and s.size >= 2),
            ):
                st.markdown(
                    f'<span class="badge {badge}">{s.family.value}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(_pills(s.avg_scores), unsafe_allow_html=True)

                if not is_healthy:
                    cause = infer_root_cause(s)
                    st.markdown(
                        f'<div class="card card-muted" style="margin-top:10px">'
                        f'<b>Root cause:</b> {cause["hypothesis"]}<br>'
                        f'<span style="color:var(--text-secondary);font-size:0.9rem">{cause["action"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("→ Go to Repair Lab", key=f"goto_{s.slice_type.value}"):
                        st.session_state["repair_eval_file"] = sel
                        st.session_state["repair_slice_label"] = s.slice_label
                        st.info("Switch to the **🛠 Repair Lab** tab.")

        st.divider()
        st.markdown("### 📄 Export Report")
        if st.button("Generate HTML report", key="export_report_btn", type="primary"):
            from repair.report import generate_html_report
            with st.spinner("Building report…"):
                html = generate_html_report(sel, cases)
            st.download_button(
                label="⬇ Download report.html",
                data=html.encode("utf-8"),
                file_name=f"rectify_report_{sel.stem}.html",
                mime="text/html",
                key="download_report_btn",
            )
            st.success("Report ready — click above to download.")

# ── Repair Lab ─────────────────────────────────────────────────────────────────
with tab_repair:
    from repair.ui import render_repair_lab
    render_repair_lab()

# ── Approval History ───────────────────────────────────────────────────────────
with tab_history:
    st.markdown("## 📋 Approval History")
    from repair.provenance import get_history
    import pandas as pd

    from repair.provenance import delete_record
    history = get_history()
    if not history:
        st.info("No approvals logged yet. Approve a repair card in **🛠 Repair Lab**.")
    else:
        st.caption(f"{len(history)} log entries")
        _ACT_ICON   = {"approved": "✅", "rejected": "❌"}
        _FAM_COLOR  = {"retrieval": "#DBEAFE", "grounding": "#FEF3C7",
                       "generation": "#EDE9FE", "abstention": "#FFE4E6"}
        _FAM_FG     = {"retrieval": "#1E40AF", "grounding": "#92400E",
                       "generation": "#5B21B6", "abstention": "#9F1239"}

        # Summary table
        rows = []
        for h in history:
            action = h.get("action", "")
            rows.append({
                "":       _ACT_ICON.get(action, "—"),
                "Slice":  h.get("slice_label", h.get("slice_type", "—")),
                "Family": h.get("family", "—"),
                "Action": action,
                "By":     h.get("approved_by") or h.get("rejected_by", "—"),
                "At":     (h.get("approved_at") or h.get("rejected_at", ""))[:19],
            })
        st.table(pd.DataFrame(rows).set_index("Slice"))

        st.divider()
        st.markdown("### Repair log")

        for i, h in enumerate(reversed(history)):
            action   = h.get("action", "")
            family   = h.get("family", "")
            icon     = _ACT_ICON.get(action, "—")
            bg       = _FAM_COLOR.get(family, "#FAF6F0")
            fg       = _FAM_FG.get(family, "#3B2008")
            at_raw   = h.get("approved_at") or h.get("rejected_at", "")
            at_str   = at_raw[:19].replace("T", " ") if at_raw else "—"
            by_str   = h.get("approved_by") or h.get("rejected_by", "—")

            with st.expander(
                f"{icon}  {h.get('slice_label', h.get('slice_type', '—'))}  ·  {at_str}  ·  {by_str}",
                expanded=(i == 0),
            ):
                ts  = h.get("approved_at") or h.get("rejected_at", "")
                cid = h.get("card_id", "")
                c1, c2, c3, c_del = st.columns([2, 2, 1, 1])
                c1.markdown(
                    f'<div style="background:{bg};border-radius:8px;padding:8px 12px">'
                    f'<div style="font-size:0.7rem;font-weight:700;color:{fg};text-transform:uppercase">{family}</div>'
                    f'<div style="font-size:0.85rem;font-weight:600;color:var(--text-primary);margin-top:2px">{h.get("label","—")}</div>'
                    f'<div style="font-size:0.72rem;color:var(--text-secondary);margin-top:2px">Stage: {h.get("pipeline_stage","—")}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                c2.markdown(
                    f'<div style="background:var(--bg-card);border-radius:8px;padding:8px 12px">'
                    f'<div style="font-size:0.7rem;font-weight:700;color:var(--text-primary)">Outcome</div>'
                    f'<div style="font-size:0.9rem;font-weight:700;color:{"#166534" if action=="approved" else "#9F1239"}">'
                    f'{icon} {action.title()}</div>'
                    f'<div style="font-size:0.72rem;color:var(--text-secondary)">By {by_str} at {at_str}</div>'
                    f'<div style="font-size:0.72rem;color:var(--text-secondary)">Scope: {h.get("scope","—")} · '
                    f'Confidence: {h.get("confidence", 0):.0%}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                affected_val = h.get("affected_cases", "—")
                c3.metric("Cases affected", len(affected_val) if isinstance(affected_val, list) else affected_val)
                if c_del.button("🗑 Delete", key=f"del_{cid}_{ts}", type="secondary", use_container_width=True):
                    if delete_record(cid, ts):
                        st.success("Entry deleted.")
                        st.rerun()
                    else:
                        st.error("Could not find entry to delete.")

                if h.get("expected_benefit"):
                    st.markdown(f"**Expected benefit:** {h['expected_benefit']}")
                if h.get("expected_tradeoff"):
                    st.markdown(f"**Trade-off:** {h['expected_tradeoff']}")
                if action == "rejected" and h.get("reason"):
                    st.markdown(f"**Rejection reason:** {h['reason']}")
                if h.get("notes"):
                    st.markdown(f"**Notes:** {h['notes']}")

                sr = h.get("sandbox_result")
                if sr:
                    st.markdown("**Sandbox result:**")
                    sr_cols = st.columns(4)
                    sr_cols[0].metric("Improved",  sr.get("improved", 0),
                                      delta=f"+{sr.get('improved',0)}", delta_color="normal")
                    sr_cols[1].metric("Unchanged", sr.get("unchanged", 0))
                    sr_cols[2].metric("Regressed", sr.get("regressed", 0),
                                      delta=f"-{sr.get('regressed',0)}", delta_color="inverse")
                    sr_cols[3].metric("Rate", f"{sr.get('improvement_rate', 0):.0%}")
                    avg_d = sr.get("avg_deltas", {})
                    if avg_d:
                        best  = max(avg_d, key=avg_d.get)
                        worst = min(avg_d, key=avg_d.get)
                        st.caption(
                            f"Biggest gain: `{best}` {avg_d[best]:+.3f}  ·  "
                            f"Biggest drop: `{worst}` {avg_d[worst]:+.3f}"
                        )
                else:
                    st.caption("No sandbox run recorded for this entry.")

                params = h.get("params", [])
                if params:
                    st.markdown("**Parameters applied:**")
                    pcols = st.columns(len(params))
                    for pc, p in zip(pcols, params):
                        pc.markdown(
                            f'<div style="background:var(--bg-card-muted);border-radius:8px;padding:8px;text-align:center">'
                            f'<div style="font-size:0.65rem;color:var(--text-secondary)">{p.get("name","")}</div>'
                            f'<div style="font-family:monospace;font-size:0.8rem;color:#9F1239">{p.get("current_value","")}</div>'
                            f'<div style="color:var(--arrow);font-size:0.8rem">→</div>'
                            f'<div style="font-family:monospace;font-size:0.8rem;color:#166534">{p.get("suggested_value","")}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                affected = h.get("affected_cases", [])
                if isinstance(affected, list) and affected:
                    with st.expander(f"Case IDs ({len(affected)})"):
                        st.markdown(", ".join(f"`{c}`" for c in affected))

