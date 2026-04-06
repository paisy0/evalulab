from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

__all__ = ["run_sql_eval", "check_sql_syntax", "check_sql_keywords"]

_SQL_STATEMENT_TYPES = (
    exp.Select, exp.Insert, exp.Update, exp.Delete,
    exp.Create, exp.Drop, exp.Alter, exp.Merge,
    exp.Use, exp.Set, exp.Show, exp.Describe, exp.Command,
    exp.Transaction, exp.Commit, exp.Rollback, exp.Grant,
)


def check_sql_syntax(sql: str) -> dict:
    if not sql or not sql.strip():
        return {"valid": False, "error": "Empty SQL"}

    try:
        parsed = sqlglot.parse(sql.strip())
    except sqlglot.errors.ParseError as e:
        return {"valid": False, "error": str(e)}
    except Exception as e:
        return {"valid": False, "error": f"Unexpected: {e}"}

    if not parsed or parsed[0] is None:
        return {"valid": False, "error": "Parser returned nothing"}

    stmt = parsed[0]
    if not isinstance(stmt, _SQL_STATEMENT_TYPES):
        return {
            "valid": False,
            "error": f"Not a SQL statement (got {type(stmt).__name__})",
        }

    return {"valid": True, "error": None}


def _contains_keyword(sql: str, keyword: str) -> bool:
    parts = [re.escape(part) for part in keyword.strip().split() if part.strip()]
    if not parts:
        return True
    pattern = r"(?<![A-Za-z0-9_])" + r"\s+".join(parts) + r"(?![A-Za-z0-9_])"
    return re.search(pattern, sql, flags=re.IGNORECASE) is not None


def check_sql_keywords(sql: str, expected: list[str]) -> dict:
    keywords = [kw.strip() for kw in expected if isinstance(kw, str) and kw.strip()]
    if not keywords:
        return {
            "checked": False,
            "all_present": False,
            "missing": [],
        }

    missing = [kw for kw in keywords if not _contains_keyword(sql, kw)]
    return {
        "checked": True,
        "all_present": len(missing) == 0,
        "missing": missing,
    }


def run_sql_eval(
    query: str,
    sql: str,
    expected_keywords: list[str] | None = None,
) -> dict:
    syntax = check_sql_syntax(sql)
    keywords = check_sql_keywords(sql, expected_keywords or [])

    passed = syntax["valid"]
    if keywords["checked"]:
        passed = passed and keywords["all_present"]

    return {
        "query": query,
        "sql": sql,
        "syntax_valid": syntax["valid"],
        "syntax_error": syntax["error"],
        "keywords_checked": keywords["checked"],
        "keywords_ok": keywords["all_present"],
        "missing_keywords": keywords["missing"],
        "passed": passed,
    }
