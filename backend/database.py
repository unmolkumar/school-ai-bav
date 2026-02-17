"""
database.py — Shared database connection for the FastAPI backend.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from contextlib import contextmanager

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_recycle=280,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"connect_timeout": 30},
)


def query(sql: str, params: dict = None):
    """Execute a SQL query and return list of dicts."""
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        cols = list(result.keys())
        return [dict(zip(cols, row)) for row in result.fetchall()]


def execute(sql: str, params: dict = None):
    """Execute a write SQL statement."""
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})
