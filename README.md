## Şu An Neyi Ölçüyor?

| Evaluator | Metrics |
| :--- | :--- |
| **Retrieval** | Precision@K · Recall@K · NDCG@K |
| **SQL** | Syntax validity · keyword presence |
| **Text** | Keyword coverage · answer length · consistency |

---

```bash
pip install -r requirements.txt
cp .env.example .env      # db cred girmek lazım.
python main.py            # demo datayla çalışıyor.

gerçek database e bağlan:
```bash
python main.py --db postgres
python main.py --db mysql --query "SELECT * FROM eval_log LIMIT 100"
```

Results are printed to the terminal and saved to `reports/` as CSV + JSON.

---
🗺️ Yol Haritası

[x] Retrieval, SQL, text evaluators + DB loader + reporter

[ ] Synthetic test data generation (RAGAS TestsetGenerator)

[ ] NDCG & MRR deep dive, embedding-based similarity

[ ] LLM-as-Judge (hallucination detection, quality scoring)

[ ] Consistency & adversarial eval

[ ] Observability (Langfuse), regression eval, full pipeline

[ ] CI/CD integration (Promptfoo), A/B testing, DeepEval (oralara gelirsek inş :D)

⚙️ DB Column Mapping
main.py'deki mapping'i şemaya uygun olarak değiştir:

mapping = {
    "user_question":   "query",
    "system_response": "answer",
    "generated_sql":   "sql",
}
