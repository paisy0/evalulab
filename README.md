# Evaluation Pipeline 

## Mevcut Kapsam

Şu anki hali:

- Retrieval evaluator
- SQL evaluator
- Text evaluator
- Postgres, MySQL ve SQLite loader'ları ya da JSON/CSV dosya
- Result reporter

Bu aşamada baktığı metrikler:

| Evaluator | Metrics |
| :--- | :--- |
| **Retrieval** | Precision@K, Recall@K, NDCG@K |
| **SQL** | Syntax validity, keyword presence |
| **Text** | Keyword coverage, answer length, consistency |


## Roadmap

### Tamamlananlar

- [x] Retrieval, SQL, text evaluators + DB loader + reporter

### Sonraki Adımlar

- [ ] Synthetic test data generation (RAGAS TestsetGenerator)
- [ ] NDCG & MRR deep dive, embedding-based similarity
- [ ] LLM-as-Judge (hallucination detection, quality scoring)
- [ ] Consistency & adversarial eval
- [ ] Observability (Langfuse), regression eval, full pipeline
- [ ] CI/CD integration (Promptfoo), A/B testing, DeepEval



## Şu an nasıl çalışıyor?

Pipeline şu akışla çalışır:

1. Postgres, MySQL veya SQLite'a bağlanır ya da JSON/CSV file okur.
2. Source query çalıştırır ya da evaluator row'larını file içinden alır.
3. DB input kullanılıyorsa DB column'larını evaluator schema'ya map eder.
4. Her row'u `type` alanına göre doğru evaluator'a yollar.
5. Dashboard çıkartır.
6. İstenirse [reports](/C:/Users/useruserseninuser/Desktop/ai-eval-lab/reports) altına CSV ve JSON report yazar.

Pipeline mevcut output'ları evaluate eder.

Evaluate edilen system outputs örnekleri:

- Retrieval output: retrieved document IDs
- SQL output: generated SQL query
- Text output: generated answer text

Bu row'ları hem database üzerinden hem de doğrudan JSON/CSV file üzerinden verebilirsin.

## Proje Yapısı

- [main.py](/C:/Users/ordox/Desktop/ai-eval-lab/main.py): entry point ve evaluator dispatch
- [src/config.py](/C:/Users/ordox/Desktop/ai-eval-lab/src/config.py): env-based config ve thresholds
- [src/loaders](/C:/Users/ordox/Desktop/ai-eval-lab/src/loaders): DB loader'ları, file loader'ları ve row normalization
- [src/evaluators](/C:/Users/ordox/Desktop/ai-eval-lab/src/evaluators): retrieval, SQL ve text evaluator'ları
- [src/pipeline/reporter.py](/C:/Users/ordox/Desktop/ai-eval-lab/src/pipeline/reporter.py): dashboard ve file export
- [tests](/C:/Users/ordox/Desktop/ai-eval-lab/tests): unit test'ler

## Kurulum

```bash
pip install -r requirements.txt
cp .env.example .env
```

İsteğe bağlı sanity check:

```bash
python setup_check.py
```

## Environment Variables

[.env.example](/C:/Users/ordox/Desktop/ai-eval-lab/.env.example) dosyasını kopyalayıp doldur:

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_SQLITE_PATH=
EVAL_SOURCE_QUERY=
EVAL_COL_QUERY=
EVAL_COL_ANSWER=
EVAL_COL_SQL=
EVAL_COL_RETRIEVED=
EVAL_COL_RELEVANT=
EVAL_COL_TYPE=
EVAL_COL_KEYWORDS=
EVAL_COL_REFERENCE_ANSWER=
EVAL_COL_K=
```

## DB Mapping

`EVAL_COL_*` alanları gerçek data değil, column name içindir.

Doğru kullanım:

```env
EVAL_COL_QUERY=user_question
EVAL_COL_ANSWER=system_response
EVAL_COL_SQL=generated_sql
```

Yanlış kullanım:

```env
EVAL_COL_QUERY=What is revenue?
EVAL_COL_SQL=SELECT * FROM orders
```

Alanların anlamı:

- `EVAL_SOURCE_QUERY`: database'den row çekmek için kullanılan SQL query
- `DB_SQLITE_PATH`: `--db sqlite` kullanıldığında SQLite file path
- `EVAL_COL_QUERY`: user question tutan column
- `EVAL_COL_ANSWER`: generated text answer tutan column
- `EVAL_COL_SQL`: generated SQL tutan column
- `EVAL_COL_RETRIEVED`: retrieved document IDs tutan column
- `EVAL_COL_RELEVANT`: relevant document IDs tutan column
- `EVAL_COL_TYPE`: evaluation type tutan column
- `EVAL_COL_KEYWORDS`: expected keywords tutan column
- `EVAL_COL_REFERENCE_ANSWER`: reference answer tutan column
- `EVAL_COL_K`: `k` value tutan column

`type` column içinde beklenen değerler:

- `retrieval`
- `sql`
- `text`

## Row Contract

Her row'da olması gerekenler:

- `query`
- `type`

`retrieval` row'ları için:

- retrieved docs
- relevant docs
- opsiyonel `k`

`sql` row'ları için:

- generated SQL
- expected keywords

`text` row'ları için:

- generated answer
- expected keywords
- reference answer

Gerekli mapping veya gerekli value eksikse pipeline boş/uydurma sonuç üretmek yerine fail-fast hata verir.

## Kabul Edilen List Formatlar:

Bu alanlar JSON array ya da comma-separated string olarak tutulabilir:

- retrieved docs
- relevant docs
- expected keywords

Örnek:

```text
["doc_1", "doc_2"]
```

```text
doc_1,doc_2
```

## Örnek Mapping

Eğer tablonda şu kolonlar varsa:

- `user_question`
- `system_response`
- `generated_sql`
- `source_doc_ids`
- `relevant_doc_ids`
- `eval_type`
- `keywords`
- `gold_answer`
- `top_k`

 `.env` şuna benzemeli:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=my_database
DB_USER=my_user
DB_PASSWORD=my_password

EVAL_SOURCE_QUERY=SELECT * FROM eval_log LIMIT 100
EVAL_COL_QUERY=user_question
EVAL_COL_ANSWER=system_response
EVAL_COL_SQL=generated_sql
EVAL_COL_RETRIEVED=source_doc_ids
EVAL_COL_RELEVANT=relevant_doc_ids
EVAL_COL_TYPE=eval_type
EVAL_COL_KEYWORDS=keywords
EVAL_COL_REFERENCE_ANSWER=gold_answer(yok ki::))
EVAL_COL_K=top_k
```

SQLite örneği:

```env
DB_SQLITE_PATH=C:\path\to\eval.sqlite
EVAL_SOURCE_QUERY=SELECT * FROM eval_log LIMIT 100
EVAL_COL_QUERY=query_text
EVAL_COL_ANSWER=answer_text
EVAL_COL_SQL=generated_sql
EVAL_COL_RETRIEVED=retrieved_docs
EVAL_COL_RELEVANT=relevant_docs
EVAL_COL_TYPE=eval_type
EVAL_COL_KEYWORDS=expected_keywords
EVAL_COL_REFERENCE_ANSWER=reference_answer
EVAL_COL_K=top_k
```

## Evaluation Nasıl Çalışıyor

### Retrieval

Input:

- query
- retrieved docs
- relevant docs
- opsiyonel `k`

Output field'ları:

- `precision_k`
- `recall_k`
- `ndcg_k`
- `passed`

### SQL

Input:

- query
- SQL
- expected keywords

Output field'ları:

- `syntax_valid`
- `syntax_error`
- `keywords_checked`
- `keywords_ok`
- `missing_keywords`
- `passed`

Not:

- SQL evaluation syntax ve gerekli keyword presence kontrolü yapar.
- SQL'i execute etmez ve query result'unun semantic correctness kısmını doğrulamaz.

### Text

Input:

- query
- answer
- expected keywords
- reference answer

Output field'ları:

- `keywords_checked`
- `keywords_ok`
- `missing_keywords`
- `length_ok`
- `word_count`
- `consistency_checked`
- `consistency_ok`
- `consistency_score`
- `passed`

## Çalıştırma

```bash
python main.py --db postgres
python main.py --db pg
python main.py --db mysql
python main.py --db sqlite
python main.py --input-json cases.json
python main.py --input-csv cases.csv
python main.py --db postgres --query "SELECT * FROM eval_log LIMIT 100"
python main.py --db postgres --no-save
```

`--query` sadece `--db` ile birlikte çalışır.

## File Input Format

`--input-json` veya `--input-csv` kullanıldığında row'lar doğrudan evaluator schema ile gelmelidir.

JSON örneği:

```json
[
  {
    "type": "retrieval",
    "query": "What is the refund policy?",
    "retrieved": ["doc_1", "doc_2"],
    "relevant": ["doc_1"],
    "k": 2
  },
  {
    "type": "sql",
    "query": "Total sales in 2024",
    "sql": "SELECT SUM(amount) FROM sales WHERE year = 2024",
    "expected_keywords": ["SELECT", "SUM", "FROM", "WHERE"]
  },
  {
    "type": "text",
    "query": "Summarize the support policy",
    "answer": "Support is available on weekdays and critical issues are prioritized.",
    "expected_keywords": ["support", "weekdays", "critical"],
    "reference_answer": "Support is available during weekdays and urgent issues are prioritized."
  }
]
```

CSV örneği:

```csv
type,query,sql,expected_keywords
sql,Total sales in 2024,"SELECT SUM(amount) FROM sales WHERE year = 2024","SELECT,SUM,FROM,WHERE"
```

JSON/CSV input için gerekli field'lar yukarıdaki row contract ile aynıdır.

## Reports

Reporter stdout'a küçük bir dashboard çıkartır ve `--no-save` kullanılmazsa şu çıktıları verir:

- `reports/eval_results_<timestamp>.csv`
- `reports/eval_results_<timestamp>.json`

## Test

Tüm testleri çalıştırmak için:

```bash
python -m pytest tests -q
```

Benim güncel test durumu: `25 passed`

## Kısıtlar

Bu repo geliştirme aşamasında.

- Output'ları evaluate eder; output üretmez.
- SQL evaluation syntax ve keyword bazlıdır, result-set bazlı değildir.
- Text consistency, reference answer column'una bağlıdır.
- Retrieval quality, database içindeki retrieved ve relevant doc ID'lerinin doğruluğuna bağlıdır.
