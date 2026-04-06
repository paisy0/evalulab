from __future__ import annotations

from pathlib import Path, PureWindowsPath

from src.config import PROJECT_ROOT

__all__ = ["display_path"]


def _filename(path: str | Path) -> str:
    return PureWindowsPath(str(path)).name or Path(str(path)).name or str(path)


def display_path(path: str | Path) -> str:
    try:
        rel = str(Path(path).resolve().relative_to(PROJECT_ROOT.resolve()))
    except (OSError, RuntimeError, ValueError):
        return _filename(path)

    if "\\" in rel:
        return _filename(path)
    return rel
