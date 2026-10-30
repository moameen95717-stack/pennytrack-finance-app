"""SQLite persistence layer for PennyTrack.

All SQL lives here. The UI only talks to the `Database` class and never
sees a cursor or a connection. Money is stored as integer paise to avoid
floating point rounding errors.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterator, List, Optional, Union

from models import EXPENSE, INCOME, Summary, Transaction

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "pennytrack.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    type         TEXT    NOT NULL CHECK (type IN ('income', 'expense')),
    amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
    category     TEXT    NOT NULL,
    description  TEXT    NOT NULL DEFAULT '',
    tx_date      TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_transactions_date
    ON transactions (tx_date DESC, id DESC);
"""

_SELECT_COLUMNS = "id, type, amount_paise, category, description, tx_date"


class DatabaseError(Exception):
    """Raised when a database operation fails."""


def _to_paise(amount: Decimal) -> int:
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _from_paise(paise: int) -> Decimal:
    return Decimal(paise) / Decimal(100)


class Database:
    """Thin, parameterized wrapper around the PennyTrack SQLite file."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)  # may raise OSError
        self._initialize()

    @property
    def path(self) -> Path:
        return self._path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = sqlite3.connect(self._path)
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            if conn is not None:
                conn.rollback()
            raise DatabaseError(str(exc)) from exc
        finally:
            if conn is not None:
                conn.close()

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    @staticmethod
    def _row_to_transaction(row: sqlite3.Row) -> Transaction:
        try:
            return Transaction(
                id=row["id"],
                type=row["type"],
                amount=_from_paise(row["amount_paise"]),
                category=row["category"],
                description=row["description"],
                date=date.fromisoformat(row["tx_date"]),
            )
        except ValueError as exc:
            raise DatabaseError(f"Corrupted transaction record (id {row['id']}): {exc}") from exc

    # ------------------------------------------------------------------ create
    def add_transaction(self, tx: Transaction) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO transactions (type, amount_paise, category, description, tx_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (tx.type, _to_paise(tx.amount), tx.category, tx.description, tx.date.isoformat()),
            )
            return int(cursor.lastrowid)

    # -------------------------------------------------------------------- read
    def get_transaction(self, tx_id: int) -> Optional[Transaction]:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT {_SELECT_COLUMNS} FROM transactions WHERE id = ?", (tx_id,)
            ).fetchone()
        return self._row_to_transaction(row) if row else None

    def get_recent(self, limit: int = 10) -> List[Transaction]:
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT {_SELECT_COLUMNS} FROM transactions "
                "ORDER BY tx_date DESC, id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [self._row_to_transaction(r) for r in rows]

    def get_all(self) -> List[Transaction]:
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT {_SELECT_COLUMNS} FROM transactions ORDER BY tx_date DESC, id DESC"
            ).fetchall()
        return [self._row_to_transaction(r) for r in rows]

    def get_summary(self) -> Summary:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT "
                "COALESCE(SUM(CASE WHEN type = ? THEN amount_paise END), 0) AS income_paise, "
                "COALESCE(SUM(CASE WHEN type = ? THEN amount_paise END), 0) AS expense_paise "
                "FROM transactions",
                (INCOME, EXPENSE),
            ).fetchone()
        return Summary(
            total_income=_from_paise(row["income_paise"]),
            total_expenses=_from_paise(row["expense_paise"]),
        )

    # ------------------------------------------------------------------ update
    def update_transaction(self, tx: Transaction) -> bool:
        """Update an existing transaction. Returns False if it no longer exists."""
        if tx.id is None:
            raise DatabaseError("Cannot update a transaction without an id.")
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE transactions "
                "SET type = ?, amount_paise = ?, category = ?, description = ?, tx_date = ? "
                "WHERE id = ?",
                (
                    tx.type,
                    _to_paise(tx.amount),
                    tx.category,
                    tx.description,
                    tx.date.isoformat(),
                    tx.id,
                ),
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------------ delete
    def delete_transaction(self, tx_id: int) -> bool:
        """Delete a transaction. Returns False if it did not exist."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
            return cursor.rowcount > 0
