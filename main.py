#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys

from src.config import get_source_config
from src.evaluators import run_retrieval_eval, run_sql_eval, run_text_eval
from src.exceptions import ConfigurationError, EvalLabError, UnknownEvalType
from src.loaders.normalizer import to_list
from src.path_utils import display_path
from src.pipeline import run_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("eval-lab")

_MISSING = object()


def _get_value(case: dict, *keys: str, default=None):
    for key in keys:
        value = case.get(key)
        if value is not None:
            return value
    return default


def _require_text(case: dict, *keys: str) -> str:
    value = _get_value(case, *keys, default=_MISSING)
    if value is _MISSING:
        raise ConfigurationError(f"Missing field: {keys[0]}")
    text = value.strip() if isinstance(value, str) else str(value).strip()
    if not text:
        raise ConfigurationError(f"Missing field: {keys[0]}")
    return text


def _require_list(case: dict, *keys: str) -> list:
    value = _get_value(case, *keys, default=_MISSING)
    if value is _MISSING:
        raise ConfigurationError(f"Missing field: {keys[0]}")
    if not isinstance(value, list):
        raise ConfigurationError(f"Invalid field: {keys[0]}")
    if not value:
        raise ConfigurationError(f"Missing field: {keys[0]}")
    return value


def _get_k(case: dict, default: int = 5) -> int:
    value = _get_value(case, "k", default=default)
    if value in (None, ""):
        return default
    if isinstance(value, int):
        if value <= 0:
            raise ConfigurationError(f"Invalid k value: {value!r}")
        return value
    try:
        parsed = int(value)
    except (TypeError, ValueError) as e:
        raise ConfigurationError(f"Invalid k value: {value!r}") from e
    if parsed <= 0:
        raise ConfigurationError(f"Invalid k value: {value!r}")
    return parsed


_DISPATCH = {
    "retrieval": lambda c: run_retrieval_eval(
        query=_require_text(c, "query"),
        retrieved=_require_list(c, "retrieved", "retrieved_docs"),
        relevant=_require_list(c, "relevant", "relevant_docs"),
        k=_get_k(c),
    ),
    "sql": lambda c: run_sql_eval(
        query=_require_text(c, "query"),
        sql=_require_text(c, "sql"),
        expected_keywords=c.get("expected_keywords"),
    ),
    "text": lambda c: run_text_eval(
        query=_require_text(c, "query"),
        answer=_require_text(c, "answer"),
        expected_keywords=c.get("expected_keywords"),
        reference_answer=c.get("reference_answer"),
    ),
}


def _require_source_column(row: dict, column: str) -> None:
    if column not in row:
        raise ConfigurationError(f"Missing column: {column}")


def _require_source_text(row: dict, column: str) -> str:
    _require_source_column(row, column)
    value = row[column]
    text = value.strip() if isinstance(value, str) else str(value).strip()
    if not text:
        raise ConfigurationError(f"Missing field: {column}")
    return text


def _require_source_list(row: dict, column: str) -> list:
    _require_source_column(row, column)
    values = to_list(row[column])
    if not values:
        raise ConfigurationError(f"Missing field: {column}")
    return values


def _validate_source_row(row: dict, source) -> None:
    eval_type = _require_source_text(row, source.type_column).lower()
    _require_source_text(row, source.query_column)
    if eval_type == "retrieval":
        if not source.retrieved_column:
            raise ConfigurationError("Missing mapping: EVAL_COL_RETRIEVED")
        if not source.relevant_column:
            raise ConfigurationError("Missing mapping: EVAL_COL_RELEVANT")
        _require_source_list(row, source.retrieved_column)
        _require_source_list(row, source.relevant_column)
        return
    if eval_type == "sql":
        if not source.sql_column:
            raise ConfigurationError("Missing mapping: EVAL_COL_SQL")
        _require_source_text(row, source.sql_column)
        return
    if eval_type == "text":
        if not source.answer_column:
            raise ConfigurationError("Missing mapping: EVAL_COL_ANSWER")
        _require_source_text(row, source.answer_column)
        return
    raise UnknownEvalType(eval_type)


def _validate_case(case: dict) -> None:
    eval_type = _require_text(case, "type").lower()
    _require_text(case, "query")
    if eval_type == "retrieval":
        _require_list(case, "retrieved", "retrieved_docs")
        _require_list(case, "relevant", "relevant_docs")
        _get_k(case)
        return
    if eval_type == "sql":
        _require_text(case, "sql")
        return
    if eval_type == "text":
        _require_text(case, "answer")
        return
    raise UnknownEvalType(eval_type)


def _evaluate(test_cases: list[dict], *, save: bool = True) -> list[dict]:
    results = []

    for case in test_cases:
        _validate_case(case)
        eval_type = _require_text(case, "type").lower()
        handler = _DISPATCH.get(eval_type)
        if handler is None:
            raise UnknownEvalType(eval_type)

        result = handler(case)
        result["eval_type"] = eval_type
        results.append(result)

    run_report(results, save=save)
    return results


def _load_from_db(db_type: str, query: str | None = None) -> list[dict]:
    from src.loaders import get_loader, normalize

    source = get_source_config()
    mapping = source.mapping()
    if not mapping:
        raise ConfigurationError("No EVAL_COL_* mappings configured.")
    if "query" not in mapping.values():
        raise ConfigurationError("EVAL_COL_QUERY is required.")
    if "type" not in mapping.values():
        raise ConfigurationError("EVAL_COL_TYPE is required.")

    sql = (query or source.query).strip()
    if not sql:
        raise ConfigurationError("Set --query or EVAL_SOURCE_QUERY.")

    log.info("loading from %s -> %s", db_type, sql[:80])

    with get_loader(db_type) as db:
        raw = db.fetch(sql)

    log.info("fetched %d rows", len(raw))
    for row in raw:
        _validate_source_row(row, source)
    return normalize(
        raw,
        mapping,
        list_columns=source.list_columns(),
        preserve_unmapped=True,
    )


def _load_from_json(path: str) -> list[dict]:
    from src.loaders import load_json_cases

    log.info("loading from json -> %s", display_path(path))
    cases = load_json_cases(path)
    log.info("loaded %d rows", len(cases))
    return cases


def _load_from_csv(path: str) -> list[dict]:
    from src.loaders import load_csv_cases

    log.info("loading from csv -> %s", display_path(path))
    cases = load_csv_cases(path)
    log.info("loaded %d rows", len(cases))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ai-eval-lab",
        description="Run the AI evaluation pipeline.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--db",
        choices=["postgres", "pg", "mysql", "sqlite"],
        default=None,
        help="DB type.",
    )
    group.add_argument(
        "--input-json",
        type=str,
        default=None,
        help="Path to a JSON file with evaluator rows.",
    )
    group.add_argument(
        "--input-csv",
        type=str,
        default=None,
        help="Path to a CSV file with evaluator rows.",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="SQL to fetch test cases from DB.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Skip CSV/JSON export.",
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=100.0,
        metavar="PCT",
        help=(
            "Exit with code 1 if the pass rate is below this percentage (0-100). "
            "Default: 100 (any failure exits non-zero)."
        ),
    )
    args = parser.parse_args()

    if not (0.0 <= args.fail_under <= 100.0):
        log.error("--fail-under must be between 0 and 100, got %s", args.fail_under)
        return 1

    if (args.input_json or args.input_csv) and args.query:
        log.error("--query works only with --db.")
        return 1

    try:
        if args.db:
            cases = _load_from_db(args.db, args.query)
        elif args.input_json:
            cases = _load_from_json(args.input_json)
        else:
            cases = _load_from_csv(args.input_csv)
    except EvalLabError as e:
        log.error("Input load failed: %s", e)
        return 1

    if not cases:
        log.error("0 test cases found. nothing to do.")
        return 1

    log.info("evaluating %d cases...", len(cases))
    try:
        results = _evaluate(cases, save=not args.no_save)
    except EvalLabError as e:
        log.error("Evaluation failed: %s", e)
        return 1

    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    pass_rate = (passed / total * 100) if total else 0.0
    log.info("done -> %d/%d passed (%.1f%%)", passed, total, pass_rate)

    if pass_rate < args.fail_under:
        log.warning("pass rate %.1f%% is below --fail-under %.1f%%", pass_rate, args.fail_under)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())