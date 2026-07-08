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

