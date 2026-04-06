from __future__ import annotations

import logging
import sqlite3

from src.config import get_db_config
from src.exceptions import ConnectionFailed, NotConnected, QueryFailed
from src.loaders.base_loader import BaseLoader
from src.path_utils import display_path

__all__ = ["SQLiteLoader"]
log = logging.getLogger(__name__)


class SQLiteLoader(BaseLoader):

    def __init__(self) -> None:
        self._conn = None
        self._cur = None

    def connect(self) -> None:
        db_cfg = get_db_config()
        if not db_cfg.sqlite_path:
            raise ConnectionFailed("sqlite", "DB_SQLITE_PATH", None, "Missing value")
        try:
            self._conn = sqlite3.connect(db_cfg.sqlite_path, timeout=db_cfg.timeout)
            self._conn.row_factory = sqlite3.Row
            self._cur = self._conn.cursor()
            log.info("sqlite connected -> %s", display_path(db_cfg.sqlite_path))
        except sqlite3.Error as e:
            raise ConnectionFailed("sqlite", display_path(db_cfg.sqlite_path), None, str(e)) from e

    def close(self) -> None:
        for resource in (self._cur, self._conn):
            try:
                if resource:
                    resource.close()
            except Exception as e:
                log.warning("cleanup error: %s", e)
        self._cur = self._conn = None
        log.info("sqlite connection closed")

    def fetch(self, query: str) -> list[dict]:
        if not self._cur:
            raise NotConnected()
        try:
            self._cur.execute(query)
            return [dict(row) for row in self._cur.fetchall()]
        except sqlite3.Error as e:
            raise QueryFailed(str(e)) from e