from __future__ import annotations

import csv
import json
from pathlib import Path

from src.exceptions import ConfigurationError
from src.loaders.normalizer import to_list
from src.path_utils import display_path

__all__ = ["load_json_cases", "load_csv_cases"]

_LIST_COLUMNS = {"retrieved", "retrieved_docs", "relevant", "relevant_docs", "expected_keywords"}


def _normalize_case_rows(rows: list[dict]) -> list[dict]:
    normalized = []

    for i, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ConfigurationError(f"Invalid row: {i}")

        case = {}
        for key, value in row.items():
            name = str(key).strip()
            case[name] = to_list(value) if name in _LIST_COLUMNS else value
        normalized.append(case)

    return normalized


def _read_json_payload(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as e:
        raise ConfigurationError(f"Input file not found: {display_path(path)}") from e
    except UnicodeDecodeError as e:
        raise ConfigurationError("Invalid JSON encoding.") from e
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON: {e.msg}") from e


def load_json_cases(path: str) -> list[dict]:
    payload = _read_json_payload(Path(path))

    if isinstance(payload, dict):
        payload = payload.get("cases")

    if not isinstance(payload, list):
        raise ConfigurationError("JSON input must be a list of rows.")

    return _normalize_case_rows(payload)


def load_csv_cases(path: str) -> list[dict]:
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ConfigurationError("CSV input must include a header row.")
            return _normalize_case_rows(list(reader))
    except FileNotFoundError as e:
        raise ConfigurationError(f"Input file not found: {display_path(path)}") from e
    except UnicodeDecodeError as e:
        raise ConfigurationError("Invalid CSV encoding.") from e
    except csv.Error as e:
        raise ConfigurationError(f"Invalid CSV: {e}") from e
