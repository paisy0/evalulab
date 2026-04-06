from __future__ import annotations

import json
import logging

__all__ = ["normalize", "to_list"]
log = logging.getLogger(__name__)


def _clean_list(values: list) -> list:
    cleaned = []
    for item in values:
        if item is None:
            continue
        if isinstance(item, str):
            item = item.strip()
            if not item:
                continue
        cleaned.append(item)
    return cleaned


def to_list(value) -> list:
    if isinstance(value, list):
        return _clean_list(value)
    if value is None:
        return []
    if not isinstance(value, str):
        return [value]

    stripped = value.strip()
    if not stripped:
        return []

    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return _clean_list(parsed)
        except (json.JSONDecodeError, ValueError):
            log.warning("value looks like JSON array but failed to parse, falling back to comma-split: %s", stripped[:80])

    return [item.strip() for item in stripped.split(",") if item.strip()]


def normalize(
    rows: list[dict],
    mapping: dict[str, str],
    *,
    list_columns: list[str] | None = None,
    preserve_unmapped: bool = False,
) -> list[dict]:
    list_cols = set(list_columns or [])
    mapped_keys = set(mapping.keys())
    result = []

    for row in rows:
        new = {}
        for src_col, dst_col in mapping.items():
            val = row.get(src_col)
            new[dst_col] = to_list(val) if dst_col in list_cols else val
        if preserve_unmapped:
            for col, val in row.items():
                if col not in mapped_keys:
                    new[col] = val
        result.append(new)

    if not result:
        log.warning("normalizer got 0 rows - nothing to transform")

    return result
