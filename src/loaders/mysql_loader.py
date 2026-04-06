from __future__ import annotations

import logging

import mysql.connector

from src.config import get_db_config
from src.exceptions import ConnectionFailed, NotConnected, QueryFailed
from src.loaders.base_loader import BaseLoader

__all__ = ["MySQLLoader"]
log = logging.getLogger(__name__)


class MySQLLoader(BaseLoader):

    def __init__(self) -> None:
        self._conn = None
        self._cur = None

    def connect(self) -> None:
        db_cfg = get_db_config()
        port = db_cfg.mysql_port
        if not db_cfg.name:
            raise ConnectionFailed("mysql", db_cfg.host, port, "DB_NAME is not set in .env")
        if not db_cfg.user:
            raise ConnectionFailed("mysql", db_cfg.host, port, "DB_USER is not set in .env")
        try:
            self._conn = mysql.connector.connect(
                host=db_cfg.host,
                port=port,
                database=db_cfg.name,
                user=db_cfg.user,
                password=db_cfg.password,
                connection_timeout=db_cfg.timeout,
            )
            self._cur = self._conn.cursor(dictionary=True)
            log.info("mysql connected -> %s:%s/%s", db_cfg.host, port, db_cfg.name)
        except mysql.connector.Error as e:
            raise ConnectionFailed("mysql", db_cfg.host, port, str(e)) from e

    def close(self) -> None:
        for resource in (self._cur, self._conn):
            try:
                if resource:
                    resource.close()
            except Exception as e:
                log.warning("cleanup error: %s", e)
        self._cur = self._conn = None
        log.info("mysql connection closed")

    def fetch(self, query: str) -> list[dict]:
        if not self._cur:
            raise NotConnected()
        try:
            self._cur.execute(query)
            return [dict(row) for row in self._cur.fetchall()]
        except mysql.connector.Error as e:
            raise QueryFailed(str(e)) from e
