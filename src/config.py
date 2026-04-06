from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from src.exceptions import ConfigurationError

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def _parse_int(env_var: str, default: int, *, min_val: int = 0, max_val: int | None = None) -> int:
    raw = os.getenv(env_var, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ConfigurationError(
            f"Invalid value for {env_var}: '{raw}' is not an integer."
        )
    if value < min_val or (max_val is not None and value > max_val):
        raise ConfigurationError(
            f"Invalid value for {env_var}: {value} is out of range ({min_val}-{max_val})."
        )
    return value


@dataclass(frozen=True)
class DBConfig:
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: _parse_int("DB_PORT", 5432, min_val=1, max_val=65535))
    name: str = field(default_factory=lambda: os.getenv("DB_NAME", ""))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    sqlite_path: str = field(default_factory=lambda: os.getenv("DB_SQLITE_PATH", "").strip())
    mysql_port: int = field(default_factory=lambda: _parse_int("DB_MYSQL_PORT", 3306, min_val=1, max_val=65535))
    timeout: int = 10

    def __repr__(self) -> str:
        return f"DBConfig({self.host}:{self.port}/{self.name}, user={self.user})"


@dataclass(frozen=True)
class EvalThresholds:
    precision_min: float = 0.5
    recall_min: float = 0.5
    ndcg_min: float = 0.5
    min_answer_words: int = 10
    max_answer_words: int = 500
    consistency_min: float = 0.80


@dataclass(frozen=True)
class EvalSourceConfig:
    query: str = field(default_factory=lambda: os.getenv("EVAL_SOURCE_QUERY", "").strip())
    query_column: str = field(default_factory=lambda: os.getenv("EVAL_COL_QUERY", "").strip())
    answer_column: str = field(default_factory=lambda: os.getenv("EVAL_COL_ANSWER", "").strip())
    sql_column: str = field(default_factory=lambda: os.getenv("EVAL_COL_SQL", "").strip())
    retrieved_column: str = field(default_factory=lambda: os.getenv("EVAL_COL_RETRIEVED", "").strip())
    relevant_column: str = field(default_factory=lambda: os.getenv("EVAL_COL_RELEVANT", "").strip())
    type_column: str = field(default_factory=lambda: os.getenv("EVAL_COL_TYPE", "").strip())
    keywords_column: str = field(default_factory=lambda: os.getenv("EVAL_COL_KEYWORDS", "").strip())
    reference_answer_column: str = field(default_factory=lambda: os.getenv("EVAL_COL_REFERENCE_ANSWER", "").strip())
    k_column: str = field(default_factory=lambda: os.getenv("EVAL_COL_K", "").strip())

    def mapping(self) -> dict[str, str]:
        pairs = (
            (self.query_column, "query"),
            (self.answer_column, "answer"),
            (self.sql_column, "sql"),
            (self.retrieved_column, "retrieved"),
            (self.relevant_column, "relevant"),
            (self.type_column, "type"),
            (self.keywords_column, "expected_keywords"),
            (self.reference_answer_column, "reference_answer"),
            (self.k_column, "k"),
        )
        return {src: dst for src, dst in pairs if src}

    def list_columns(self) -> list[str]:
        columns = []
        if self.retrieved_column:
            columns.append("retrieved")
        if self.relevant_column:
            columns.append("relevant")
        if self.keywords_column:
            columns.append("expected_keywords")
        return columns


def get_source_config() -> EvalSourceConfig:
    return EvalSourceConfig()


def get_db_config() -> DBConfig:
    return DBConfig()


def get_thresholds() -> EvalThresholds:
    return EvalThresholds()


thresholds = EvalThresholds()
