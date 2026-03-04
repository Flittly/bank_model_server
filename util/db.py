from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

import config


@contextmanager
def get_db_connection(*, autocommit: bool = False, dict_cursor: bool = False):
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        dbname=config.DB_NAME,
    )
    conn.autocommit = autocommit
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_db_cursor(*, autocommit: bool = False, dict_cursor: bool = False):
    with get_db_connection(autocommit=autocommit, dict_cursor=dict_cursor) as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        with conn.cursor(cursor_factory=cursor_factory) as cursor:
            try:
                yield conn, cursor
                if not autocommit:
                    conn.commit()
            except Exception:
                if not autocommit:
                    conn.rollback()
                raise
