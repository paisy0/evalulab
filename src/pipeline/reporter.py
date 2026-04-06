from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path

from src.config import REPORTS_DIR
from src.path_utils import display_path

__all__ = ["run_report"]
log = logging.getLogger(__name__)


def _make_path(ext: str, ts: str, directory: Path = REPORTS_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"eval_results_{ts}.{ext}"


def _save_csv(results: list[dict], path: Path) -> None:
    all_keys = sorted({k for r in results for k in r})
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in all_keys})
    log.info("csv -> %s", display_path(path))


def _save_json(results: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    log.info("json -> %s", display_path(path))


def _print_dashboard(results: list[dict]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r.get("passed") is True)
    failed = total - passed
    rate = passed / total if total else 0

    type_stats: dict[str, dict] = {}
    for r in results:
        et = r.get("eval_type", "unknown")
        if et not in type_stats:
            type_stats[et] = {"total": 0, "passed": 0}
        type_stats[et]["total"] += 1
        if r.get("passed") is True:
            type_stats[et]["passed"] += 1

    retrieval_results = [r for r in results if r.get("eval_type") == "retrieval"]
    avg_precision = avg_recall = avg_ndcg = None
    if retrieval_results:
        avg_precision = sum(r.get("precision_k", 0) for r in retrieval_results) / len(retrieval_results)
        avg_recall = sum(r.get("recall_k", 0) for r in retrieval_results) / len(retrieval_results)
        avg_ndcg = sum(r.get("ndcg_k", 0) for r in retrieval_results) / len(retrieval_results)

    print()
    print("=" * 52)
    print("  EVAL DASHBOARD")
    print("=" * 52)
    print(f"  Total   : {total}")
    print(f"  Passed  : {passed}")
    print(f"  Failed  : {failed}")
    print(f"  Rate    : {rate:.1%}")
    print(f"  Time    : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("-" * 52)

    print("  Breakdown:")
    for et, stats in sorted(type_stats.items()):
        t_total = stats["total"]
        t_passed = stats["passed"]
        t_rate = t_passed / t_total if t_total else 0
        print(f"    {et:12s} : {t_passed}/{t_total} ({t_rate:.0%})")

    if avg_precision is not None:
        print("-" * 52)
        print("  Retrieval Averages:")
        print(f"    Precision@K : {avg_precision:.4f}")
        print(f"    Recall@K    : {avg_recall:.4f}")
        print(f"    NDCG@K      : {avg_ndcg:.4f}")

    print("=" * 52)

    if failed:
        print("\n  [FAIL] Failed:")
        for r in results:
            if not r.get("passed"):
                q = r.get("query", "?")
                t = r.get("eval_type", "?")
                print(f"    [{t}] {q}")
    print()


def run_report(results: list[dict], *, save: bool = True) -> dict | None:
    if not results:
        log.warning("no results to report")
        return None

    _print_dashboard(results)

    if not save:
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = _make_path("csv", ts)
    json_path = _make_path("json", ts)
    _save_csv(results, csv_path)
    _save_json(results, json_path)

    print(f"  Reports saved:")
    print(f"    CSV  -> {csv_path}")
    print(f"    JSON -> {json_path}")
    print()

    return {"csv": display_path(csv_path), "json": display_path(json_path)}
