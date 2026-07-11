# Rectify Synthetic Dataset Schema

This pack contains three complementary dataset artifacts for **Rectify / RAGVue Repair**.

## Files

- `corpus.jsonl` — synthetic source documents for the reference RAG pipeline
- `questions_100.jsonl` — 100-question evaluation plan over the corpus.

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

## Recommended usage

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
