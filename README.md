# AI Eval Pipeline MVP'ish

## -güncel durum: metin değerlendirmesi için geliştirme ve araştırma yapıyorum-

Şu an olanlar:

- Retrieval evaluator
- SQL evaluator
- Text evaluator
- Postgres, MySQL ve SQLite loader'ları
- JSON/CSV file input
- Result reporter

Bu aşamada baktığı metrikler:

| Evaluator | Metrikler |
| :--- | :--- |
| **Retrieval** | Precision@K, Recall@K, NDCG@K |
| **SQL** | Syntax validity, keyword presence |
| **Text** | Keyword coverage, answer length, consistency |

## Kısıtlar (Aktif)

- Hiçbir şey üretmez. Yani bir LLM'e bağlanıp cevap almaz, veritabanında SQL sorgusu çalıştırıp sonuç üretmez. Asıl sistem bir soruya cevap verdiyse, bir SQL generate ettiyse veya RAG sistemin bazı dokümanlar getirdiyse; bu araç sadece o kayıtları DB'den veya bir JSON/CSV'den okur, kendi kurallarından geçirir ve sisteme "şunlarda başarılısın, şunlarda rezilsin" diyen bir karne çıkartır.

- Hatasızlığa Zorlar. Kolon eksikse ya da tanımlar bozuksa geçip "0 aldı" demek yerine direkt sistemi patlatıp hatayı gösteriyor, bu da false-positive değerlendirmelerin önüne geçer(?).

- SQL evaluation syntax ve keyword bazlıdır, result-set bazlı değildir.

- Text consistency, reference answer column'una bağlıdır (varsa).

- Retrieval quality, database içindeki retrieved ve relevant doc ID'lerinin doğruluğuna bağlıdır.

  ```
  Örn. Referans: "Sunucu çöktü."
  Yapay Zekanın Cevabı: "Server kapandı."
  ```

  SequenceMatcher bu ikisini farklı görüp FAIL verebilir.

- Modern pipeline'larda metin tutarlılığı (consistency), LLM as a Judge kullanılarak anlamsal olarak yapıyormuş, ben nasıl yapabilirim bakacağım.

- SQL Değerlendirmesi Execution Yapmıyor: Araç sadece "SELECT id FROM uyeler" doğru bir SQL syntax'ı mı? diye bakıyor. Asıl veritabanında id diye bir kolon var mı veya çalıştırıldığında hata veriyor mu kontrol edemiyor. Doğruluk (Accuracy) denetimi yok, sadece şekil denetimi var.

- Keyword matching token bazlıdır, kök/çekim farkı eşleşmiyor: `"refund"` ≠ `"refunds"`, keyword yazarken cevaptaki tam formu kullanmak gerekir.

- `check_sql_keywords()` boş keyword listesi: `all_present: False` döner, `checked: False`. yani "kontrol edilmedi" anlamına gelir. pipeline zaten `checked` flag'ine baktığı için pratikte sorun yaratmıyor.

## Düzeltilen ve Eklenen Şeyler :D

- ~~Metin Değerlendirmesi Fazla İlkel (Lexical vs. Semantic): text_eval içinde kullanılan difflib.SequenceMatcher sadece harf ve kelime eşleşmesine bakar.~~
  - ✅ iyileştirildi: artık karakter bazlı değil kelime bazlı karşılaştırıyor. hâlâ anlamsal değil ama eskisi kadar mağara adamı da değil.

- ~~Eğer testlerin hiçbiri geçemezse bile kodun sonunda süreç Exit Code 0 ile sorunsuzmuş gibi kapanıyor.~~
  - ✅ düzeltildi: test başarısızsa artık exit 1 dönüyor. ayrıca `--fail-under 80` gibi kullanılabilen bir flag eklendi, pass rate bu yüzdenin altındaysa exit 1 verir, default 100 (herhangi bir failure exit 1 döner).

- ~~Regex lookbehind sorunu: keyword kontrolü `[A-Z0-9_]` kullanıyordu, `re.IGNORECASE` lookbehind'ı etkilemediği için küçük harfli kelimelerin içinde yanlış eşleşme yapıyordu. (`"preselect"` içinde `"select"` buluyordu örneğin.)~~
  - ✅ düzeltildi: `[A-Za-z0-9_]` olarak güncellendi. (`sql_eval.py`, `text_eval.py`)

- ~~`UnknownEvalType` boş parametre: `query` parametresi alıyordu ama hata mesajında hiç kullanmıyordu.~~
  - ✅ düzeltildi: boş parametre kaldırıldı. (`src/exceptions.py`)

- ~~`run_tests.py` gereksiz script: sadece `pytest tests -q`'yu subprocess ile sarıyordu, doğrudan pytest çalıştırmaktan farkı yoktu.~~
  - ✅ silindi. artık testler için direkt `python -m pytest tests -q` kullanılabilir.

- ~~Keyword Matching büyük/küçük harf farkına bakıyordu: `"select"` → `"SELECT"` eşleşmiyordu.~~
  - ✅ düzeltildi: büyük/küçük harf farkı artık yok sayılıyor.

- ~~SQL evaluator çoklu statement'ı valid sayıyordu: `SELECT 1; DROP TABLE x` gibi birden fazla statement içeren output `syntax_valid: True` alabiliyordu.~~
  - ✅ düzeltildi: birden fazla statement gelirse `syntax_valid: False` döner. (`sql_eval.py`)

- ~~File input alias eksikliği: JSON/CSV'de `retrieved_docs` veya `relevant_docs` anahtarı kullanılırsa list normalization uygulanmıyor, comma-separated string gelince validation patlar.~~
  - ✅ düzeltildi: `_LIST_COLUMNS` artık `retrieved_docs` ve `relevant_docs` alias'larını da kapsıyor. (`src/loaders/file_loader.py`)

- ~~Duplicate retrieved ID'ler recall ve NDCG'yi 1.0'ın üstüne çıkartabiliyordu: `retrieved=["doc1","doc1"]` ve `relevant=["doc1"]` gelince recall=2.0 dönüyordu.~~
  - ✅ düzeltildi: `retrieved[:k]` artık deduplicate ediliyor, aynı ID ikinci kez sayılmıyor. (`src/evaluators/retrieval_eval.py`)

- ~~DB loader'ları config'i import anında snapshot alıyordu: `from src.config import db as db_cfg` ile frozen singleton kullanılıyordu.~~
  - ✅ düzeltildi: loader'lar artık `connect()` çağrısında `get_db_config()` factory'yi kullanıyor. (`postgres_loader.py`, `mysql_loader.py`, `sqlite_loader.py`)

- ~~`--fail-under` sınır kontrolü yoktu: `-1` veya `150` gibi geçersiz değerler sessizce çalışıyordu.~~
  - ✅ düzeltildi: 0-100 dışında değer gelirse argüman parse sonrası hata verip exit 1 dönüyor. (`main.py`)

- ~~DB loader'ların fetch exception handler'ları eksikti: DB hatası olunca sessizce kesiliyordu.~~
  - ✅ düzeltildi: postgres, mysql ve sqlite loader'ları artık `QueryFailed` fırlatıyor.

- ~~MySQL loader farklı return type döndürüyordu: postgres ve sqlite `[dict(row) for row in ...]` dönerken mysql raw `fetchall()` döndürüyordu.~~
  - ✅ düzeltildi: üçü de artık `[dict(row) for row in ...]` döner.

- ~~DB port validation yoktu: `-1` veya `999999` gibi geçersiz port değerleri config'den geçiyordu.~~
  - ✅ düzeltildi: port 1-65535 aralığında olmalı, dışında `ConfigurationError` fırlatılıyor.

- ~~`to_list()` JSON parse hatalarını sessizce yutuyordu: `[doc1, doc2]` gibi geçersiz JSON array gelince uyarı vermeden comma-split'e fallback yapıyordu.~~
  - ✅ düzeltildi: artık warning logu basıyor.

- ~~`setup_check.py` gereksiz script: dependency check'ini zaten import hataları yapıyor, `.env` kontrolü de opsiyonel.~~
  - ✅ silindi.

- ~~`retrieval_eval.py` return dict'inde `"passed"` key'i eksikti.~~
  - ✅ düzeltildi: artık threshold karşılaştırması yapıp `"passed"` dönüyor.

- ~~`main.py` truncated: `log.info`, return statement ve `if __name__` bloğu eksikti.~~
  - ✅ düzeltildi: tamamlandı, pass rate kontrolü ve exit code logic'i eklendi.

## Quick Start

Repo'yu clone'ladıktan sonra hızlıca denemek için:

```bash
pip install -r requirements.txt
python main.py --input-json examples/sample_mixed.json
```

Bu komut, `examples/` altındaki örnek veriyi okuyup evaluation dashboard'unu gösterir ve `reports/` altına CSV + JSON çıktı yazar.

Daha fazla örnek:

```bash
python main.py --input-json examples/sample_mixed.json --no-save
python main.py --input-csv examples/sample_mixed.csv
```

## Roadmap

### Tamamlananlar

- [x] Retrieval, SQL, text evaluator'lar + DB loader + reporter

### Sonraki Adımlar

- [ ] Synthetic test data generation (RAGAS TestsetGenerator)
- [ ] NDCG & MRR deep dive, embedding-based similarity
- [ ] LLM-as-Judge (hallucination detection, quality scoring)
- [ ] Consistency & adversarial eval
- [ ] Observability (Langfuse), regression eval, full pipeline
- [ ] CI/CD integration (Promptfoo), A/B testing, DeepEval

## Şu An Nasıl Çalışıyor

Pipeline şu akışla çalışır:

1. Postgres, MySQL veya SQLite'a bağlanır ya da JSON/CSV file okur.
2. Source query çalıştırır ya da evaluator row'larını file içinden alır.
3. DB input kullanılıyorsa DB column'larını evaluator schema'ya map eder.
4. Her row'u `type` alanına göre doğru evaluator'a yollar.
5. Dashboard çıkartır (toplam, tür bazlı breakdown, retrieval ortalamaları).
6. İstenirse `reports/` altına CSV ve JSON report yazar.

Pipeline mevcut output'ları evaluate eder.

Evaluate edilen system output örnekleri:

- Retrieval output: retrieved document ID'ler
- SQL output: generate edilmiş SQL query
- Text output: generate edilmiş answer text

Bu row'ları hem database üzerinden hem de doğrudan JSON/CSV file üzerinden verebiliriz.

## Proje Yapısı

- [`main.py`](main.py): entry point ve evaluator dispatch
- [`src/config.py`](src/config.py): env-based config ve threshold'lar
- [`src/loaders`](src/loaders): DB loader'ları, file loader'ları ve row normalization
- [`src/evaluators`](src/evaluators): retrieval, SQL ve text evaluator'ları
- [`src/pipeline/reporter.py`](src/pipeline/reporter.py): dashboard ve file export
- [`examples`](examples): örnek JSON/CSV input dosyaları
- [`tests`](tests): unit test'ler

## Kurulum

```bash
pip install -r requirements.txt
cp .env.example .env
```

## Environment Variables

[`.env.example`](.env.example) dosyasını kopyalayıp doldur:

```env
# --- Postgres / MySQL ---
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=

# --- MySQL (ayrı port, default 3306) ---
DB_MYSQL_PORT=

# --- SQLite ---
DB_SQLITE_PATH=

# --- Evaluation Source ---
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
- `DB_MYSQL_PORT`: MySQL bağlantısı için port (default: 3306)
- `EVAL_COL_QUERY`: user question tutan column
- `EVAL_COL_ANSWER`: generated text answer tutan column
- `EVAL_COL_SQL`: generated SQL tutan column
- `EVAL_COL_RETRIEVED`: retrieved document ID'ler tutan column
- `EVAL_COL_RELEVANT`: relevant document ID'ler tutan column
- `EVAL_COL_TYPE`: evaluation type tutan column
- `EVAL_COL_KEYWORDS`: expected keyword'ler tutan column (opsiyonel)
- `EVAL_COL_REFERENCE_ANSWER`: reference answer tutan column (opsiyonel)
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

- retrieved docs (**zorunlu**)
- relevant docs (**zorunlu**)
- opsiyonel `k`

`sql` row'ları için:

- generated SQL (**zorunlu**)
- expected keywords (opsiyonel — verilmezse sadece syntax kontrolü yapılır)

`text` row'ları için:

- generated answer (**zorunlu**)
- expected keywords (opsiyonel — verilmezse keyword kontrolü atlanır)
- reference answer (opsiyonel — verilmezse consistency kontrolü atlanır)

Gerekli mapping veya gerekli value eksikse pipeline boş veya uydurma sonuç üretmek yerine fail-fast hata verir.

## Kabul Edilen List Formatları

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

Eğer tabloda şu kolonlar varsa:

- `user_question`
- `system_response`
- `generated_sql`
- `source_doc_ids`
- `relevant_doc_ids`
- `eval_type`
- `keywords`
- `gold_answer`
- `top_k`

`.env` şu şekilde olabilir:

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
EVAL_COL_REFERENCE_ANSWER=gold_answer
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
- expected keywords (opsiyonel)

Output field'ları:

- `syntax_valid`
- `syntax_error`
- `keywords_checked`
- `keywords_ok`
- `missing_keywords`
- `passed`

Not:

- SQL evaluation syntax ve gerekli keyword presence kontrolü yapar.
- Keywords verilmezse sadece syntax geçerliliği kontrol edilir.
- SQL'i execute etmez ve query result'unun semantic correctness kısmını doğrulamaz.

### Text

Input:

- query
- answer
- expected keywords (opsiyonel)
- reference answer (opsiyonel)

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

Not:

- Keywords verilmezse keyword kontrolü atlanır.
- Reference answer verilmezse consistency kontrolü atlanır.
- Passed hesabı sadece verilen kontrollere bakar.

## Çalıştırma

```bash
# Database'den
python main.py --db postgres
python main.py --db pg
python main.py --db mysql
python main.py --db sqlite
python main.py --db postgres --query "SELECT * FROM eval_log LIMIT 100"

# File'dan
python main.py --input-json cases.json
python main.py --input-csv cases.csv

# Örnek veri ile hızlı deneme
python main.py --input-json examples/sample_mixed.json

# Report kaydetmeden
python main.py --db postgres --no-save

# CI/CD için pass rate threshold'u belirle
python main.py --input-json cases.json --fail-under 80
```

`--query` sadece `--db` ile birlikte çalışır.

`--fail-under` 0-100 arası bir yüzde alır. default 100 (herhangi bir failure exit 1 döner).


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
    "query": "Total sales in 2026",
    "sql": "SELECT SUM(amount) FROM sales WHERE year = 2026",
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
sql,Total sales in 2026,"SELECT SUM(amount) FROM sales WHERE year = 2026","SELECT,SUM,FROM,WHERE"
```

JSON/CSV input için gerekli field'lar yukarıdaki row contract ile aynıdır.

## Reports

Reporter stdout'a bir dashboard çıkartır ve `--no-save` kullanılmadıysa `reports/` altına CSV ve JSON dosyaları yazar.

```
====================================================
  EVAL DASHBOARD
====================================================
  Total   : 8
  Passed  : 7
  Failed  : 1
  Rate    : 87.5%
  Time    : 2026-04-06 22:28
----------------------------------------------------
  Breakdown:
    retrieval    : 2/3 (67%)
    sql          : 3/3 (100%)
    text         : 2/2 (100%)
----------------------------------------------------
  Retrieval Averages:
    Precision@K : 0.3889
    Recall@K    : 0.6667
    NDCG@K      : 0.6399
====================================================

  [FAIL] Failed:
    [retrieval] What are the business hours?
```

## Testler

```bash
python -m pytest tests -q
```