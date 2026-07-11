# Rectify Synthetic Dataset Schema

This pack contains three complementary dataset artifacts for **Rectify / RAGVue Repair**.

## Files

- `corpus.jsonl` — synthetic source documents for the reference RAG pipeline
- `questions_100.jsonl` — 100-question evaluation plan over the corpus
- `synthetic_failure_cases_30.jsonl` — manually crafted failure cases for sanity-checking failure families, sub-clusters, and repair logic
- `README_for_code_assistant.md` — implementation/build instructions for a coding assistant

---

## 1) `corpus.jsonl`

One JSON object per line.

### Required fields
- `doc_id` (string): unique document identifier
- `title` (string): display title
- `text` (string): raw source text to index
- `type` (string): one of `company`, `person`, `product`, `event`, `summary`

### Example
```json
{"doc_id":"doc_company_01","title":"NorthRiver Analytics","text":"NorthRiver Analytics is an analytics company headquartered in Dublin. It was founded in 2016 by Elena Park. Its flagship product is RiverLens, which launched in 2019. In 2021, NorthRiver Analytics acquired Delta Insight, a company based in Berlin.","type":"company"}
```

---

## 2) `questions_100.jsonl`

One JSON object per line.

### Required fields
- `question_id` (string): unique question identifier
- `question` (string): natural-language question
- `question_type` (string): one of `factoid`, `multi_part`, `multi_hop`, `multi_hop_unanswerable`, `temporal`, `temporal_unanswerable`, `comparison`, `unanswerable`
- `is_answerable` (boolean): whether the corpus contains enough evidence to answer
- `relevant_doc_ids` (list[string]): document ids likely needed to answer
- `expected_answer` (string or null): optional expected answer for human sanity-checking
- `notes` (string): optional comments

### Example
```json
{"question_id":"q_001","question":"Who founded NorthRiver Analytics?","question_type":"factoid","is_answerable":true,"relevant_doc_ids":["doc_company_01"],"expected_answer":"Elena Park","notes":""}
```

---

## 3) `synthetic_failure_cases_30.jsonl`

This file is for **logic testing**, not for baseline retrieval.
Contexts and answers are manually constructed to trigger specific failure families.

### Required fields
- `case_id` (string): unique synthetic case id
- `question` (string)
- `contexts` (list[string]): manually supplied retrieved contexts
- `answer` (string): model answer to evaluate
- `intended_family` (string): one of `retrieval`, `grounding`, `synthesis`, `abstention`, `quality`, `instability`
- `intended_subcluster` (string): expected finer-grained pattern label
- `notes` (string): why the case belongs in that family

### Example
```json
{"case_id":"s_006","question":"When did RiverLens launch?","contexts":["RiverLens launched in 2019."],"answer":"RiverLens launched in 2020.","intended_family":"grounding","intended_subcluster":"temporal_misattribution","notes":"Unsupported date shift."}
```

---

## Recommended usage

### Logic-testing stage
Use `synthetic_failure_cases_30.jsonl` to test:
- macro failure family routing
- sub-cluster labels
- root-cause hypotheses
- repair-card generation

### End-to-end RAG stage
Use `corpus.jsonl` + `questions_100.jsonl` to:
1. index the corpus
2. run a baseline RAG pipeline
3. evaluate with RAGVue
4. route cases into failure families
5. discover sub-clusters
6. propose repairs
7. rerun the affected subset
8. compare deltas
