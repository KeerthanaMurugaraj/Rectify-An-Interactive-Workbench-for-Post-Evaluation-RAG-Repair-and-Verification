# Rectify - An Interactive Post-evaluation Workbench for RAG pipeline diagnosis, repair, and verification.

Rectify sits downstream of your RAG evaluator. It takes per-case evaluation results, groups failures by root cause into named repair slices, proposes config-level fixes, lets you approve and edit them, reruns only the broken cases, and shows a verified before/after delta report.

---

## Why Rectify?

Most RAG evaluation tools tell you *what score a case got*. They do not tell you:
- Which cases share the same root cause
- What specifically to change in your pipeline
- Whether the change actually helped

Rectify closes that loop.

| | RAGVue / RAGAS / ARES | Rectify |
|---|---|---|
| Per-case failure scores | ✓ | ✓ |
| Group cases by root cause | ✗ | ✓ |
| Suggest a specific config fix | ✗ | ✓ |
| Developer approval before applying | ✗ | ✓ |
| Verified before/after delta | ✗ | ✓ |
| Compound failure detection | ✗ | ✓ |

---

## How It Works

```
Baseline RAG run
      ↓
Evaluate with RAGVue 
      ↓
Route each case into a macro failure family
      ↓
Assign a named repair slice within the family
      ↓
Detect compound failures (secondary family)
      ↓
Generate a repair card (config patch)
      ↓
Developer inspects, approves or edits
      ↓
Sandbox rerun on affected cases only
      ↓
Before/after delta report
```

### Two-layer failure routing

**Layer 1 — 4 macro families** (deterministic, priority-ordered):

| Family | Primary signal |
|---|---|
| Abstention | Model answers when it should refuse |
| Retrieval | Evidence quality or coverage problems |
| Grounding | Answer is unfaithful to retrieved context |
| Generation | Clarity, coherence, or completeness degraded |

**Layer 2 — 23 named repair slices** within each family (e.g. R2 Noisy retrieval, G2 Entity substitution, Q3 Internal inconsistency, S1 Partial aspect coverage).

**Secondary family detection** — when two families co-fire, Rectify generates a compound repair card that patches both layers at once.

## Quick Start

```bash
git clone git@github.com:KeerthanaMurugaraj/Rectify-An-Interactive-Workbench-for-Post-Evaluation-RAG-Repair-and-Verification.git
cd Rectify
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Three sample eval files are included in `evals/` — load any of them from the **Upload / Load** tab to explore the full workflow instantly with no setup.

## App Tabs

| Tab | What it does |
|---|---|
| **📂 Upload / Load** | Select one of the included eval files or upload your own RAGVue JSON |
| **🔎 Case Explorer** | Inspect every case: query · contexts · generated answer · gold answer · scores · config — filterable by family, retriever, verdict |
| **🔍 Diagnose** | Slice breakdown by family, avg scores, root cause per slice — export HTML report |
| **🛠 Repair Lab** | Full repair workflow — inspect, approve, run sandbox, view before/after answer comparison |
| **📈 Delta Explorer** | Persisted before/after metric deltas for every sandbox run across sessions |
| **📋 Approval History** | Audit log of all approved and rejected repairs with sandbox outcome |

---

## Repair Cards

Each repair slice produces a repair card with:
- A short label and rationale
- Editable config parameters (current → suggested value)
- Expected benefit and expected tradeoff
- Confidence score (scales with slice size)
- Scope: entire slice or single case

**7 patchable config params:** `retriever_top_k` · `chunk_size` · `chunk_overlap` · `reranker_enabled` · `prompt_mode` · `abstain_if_unsupported` · `temperature`

**7 prompt modes:** `normal` · `grounded` · `citation_only` · `multi_step` · `structured_output` · `abstain_aware` · `explicit_citation`

---

## Optional: LLM Explanations

The Repair Lab has a "Generate explanation" button that calls an LLM to summarise a slice in plain language. This is optional and requires an Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your_key_here
```
Without a key, the button falls back to a deterministic summary. The explanation agent does not affect routing, slicing, or repair decisions.

## Key Design Principles

- **Rule-based routing, not ML clustering** — fully deterministic, reproducible, no training data
- **LLM for explanation only** — does not route or decide
- **Config patches only** — repairs are parameter changes, never code mutations
- **Developer at the decision point** — no repair is applied without explicit approval
- **Provenance as a first-class output** — every decision is logged with who, when, and measured effect