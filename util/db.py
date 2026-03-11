from contextlib import contextmanager
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

import config


def decimal_to_float(value, cur):
    """
    psycopg2 类型转换器：将 Decimal 转换为 float
    """
    if value is not None:
        return float(value)
    return None


# 注册 Decimal 类型转换器
DECIMAL2FLOAT = psycopg2.extensions.new_type(
    (1700,),  # DECIMAL 的 OID
    "DECIMAL2FLOAT",
    decimal_to_float,
)
psycopg2.extensions.register_type(DECIMAL2FLOAT)


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
