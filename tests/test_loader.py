import sqlite3

import pytest

from src.config import DBConfig
from src.exceptions import UnknownLoader
from src.loaders import sqlite_loader
from src.loaders.loader_factory import get_loader
from src.loaders.mysql_loader import MySQLLoader
from src.loaders.normalizer import normalize
from src.loaders.postgres_loader import PostgresLoader
from src.loaders.sqlite_loader import SQLiteLoader


def test_get_loader_returns_registered_loader():
    assert isinstance(get_loader("postgres"), PostgresLoader)
    assert isinstance(get_loader("pg"), PostgresLoader)
    assert isinstance(get_loader("mysql"), MySQLLoader)
    assert isinstance(get_loader("sqlite"), SQLiteLoader)


def test_get_loader_rejects_unknown_type():
    with pytest.raises(UnknownLoader):
        get_loader("oracle")


def test_normalize_preserves_unmapped_columns():
    rows = [
        {
            "question_col": "q",
            "retrieved_col": "doc_1,doc_2",
            "relevant_col": '["doc_1"]',
            "type_col": "retrieval",
            "extra_col": "x",
        }
    ]
    mapping = {
        "question_col": "query",
        "retrieved_col": "retrieved",
        "relevant_col": "relevant",
        "type_col": "type",
    }

    [row] = normalize(
        rows,
        mapping,
        list_columns=["retrieved", "relevant"],
        preserve_unmapped=True,
    )

    assert row["query"] == "q"
    assert row["retrieved"] == ["doc_1", "doc_2"]
    assert row["relevant"] == ["doc_1"]
    assert row["extra_col"] == "x"


def test_sqlite_loader_fetches_rows(tmp_path, monkeypatch):
    db_path = tmp_path / "eval.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE eval_log (query_col TEXT, type_col TEXT)")
    conn.execute(
        "INSERT INTO eval_log (query_col, type_col) VALUES (?, ?)",
        ("q", "retrieval"),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(
        sqlite_loader,
        "get_db_config",
        lambda: DBConfig(sqlite_path=str(db_path)),
    )

    with SQLiteLoader() as db:
        rows = db.fetch("SELECT query_col, type_col FROM eval_log")

    assert len(rows) == 1
    assert rows[0]["query_col"] == "q"
    assert rows[0]["type_col"] == "retrieval"