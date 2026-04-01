## Şu An Neyi Ölçüyor?

| Evaluator | Metrics |
| :--- | :--- |
| **Retrieval** | Precision@K · Recall@K · NDCG@K |
| **SQL** | Syntax validity · keyword presence |
| **Text** | Keyword coverage · answer length · consistency |

---
🗺️ Yol Haritası

[x] Retrieval, SQL, text evaluators + DB loader + reporter

[ ] Synthetic test data generation (RAGAS TestsetGenerator)

[ ] NDCG & MRR deep dive, embedding-based similarity

[ ] LLM-as-Judge (hallucination detection, quality scoring)

[ ] Consistency & adversarial eval

[ ] Observability (Langfuse), regression eval, full pipeline

[ ] CI/CD integration (Promptfoo), A/B testing, DeepEval (oralara gelirsek inş :D)

---
```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Gerçek DB'ye bağlan:
```bash
python main.py --db postgres
python main.py --db pg              # postgres kısaltması
python main.py --db mysql --query "SELECT * FROM eval_log LIMIT 100"
python main.py --no-save            # CSV/JSON export yapmaz
```
---

⚙️ DB Column Mapping
main.py'deki mapping'i şemaya uygun olarak değiştir:

mapping = {
    "user_question":    "query",
    "system_response":  "answer",
    "generated_sql":    "sql",
    "source_doc_ids":   "retrieved_docs",
    "relevant_doc_ids": "relevant_docs",
    "eval_type":        "type",
    "keywords":         "expected_keywords",
}
