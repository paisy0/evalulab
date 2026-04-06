from __future__ import annotations

import logging

import psycopg2
import psycopg2.extras

from src.config import db as db_cfg
from src.exceptions import ConnectionFailed, NotConnected, QueryFailed
from src.loaders.base_loader import BaseLoader

__all__ = ["PostgresLoader"]
log = logging.getLogger(__name__)


class PostgresLoader(BaseLoader):

    def __init__(self) -> None:
        self._conn = None
        self._cur = None

    def connect(self) -> None:
        if not db_cfg.name:
            raise ConnectionFailed("postgres", db_cfg.host, db_cfg.port, "DB_NAME is not set in .env")
        if not db_cfg.user:
            raise ConnectionFailed("postgres", db_cfg.host, db_cfg.port, "DB_USER is not set in .env")
        try:
            self._conn = psycopg2.connect(
                host=db_cfg.host,
                port=db_cfg.port,
                dbname=db_cfg.name,
                user=db_cfg.user,
                password=db_cfg.password,
                connect_timeout=db_cfg.timeout,
            )
            self._cur = self._conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            log.info("pg connected -> %s:%s/%s", db_cfg.host, db_cfg.port, db_cfg.name)
        except psycopg2.OperationalError as e:
            raise ConnectionFailed("postgres", db_cfg.host, db_cfg.port, str(e)) from e

    def close(self) -> None:
        for resource in (self._cur, self._conn):
            try:
                if resource:
                    resource.close()
            except Exception as e:
                log.warning("cleanup error: %s", e)
        self._cur = self._conn = None
        log.info("pg connection closed")

    def fetch(self, query: str) -> list[dict]:
        if not self._cur:
            raise NotConnected()
        try:
            self._cur.execute(query)
            return [dict(row) for row in self._cur.fetchall()]
        except psycopg2.Error as e:
            raise QueryFailed(query[:200], str(e)) from e
