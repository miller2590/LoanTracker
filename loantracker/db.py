from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Generator

from .models import Loan, Payment, Scenario


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def init(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    principal REAL NOT NULL,
                    apr REAL NOT NULL,
                    minimum_payment REAL NOT NULL,
                    start_date TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    payment_date TEXT NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    extra_monthly REAL NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
                );
                """
            )

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


class LoanRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, loan: Loan) -> Loan:
        with self.db._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO loans (name, principal, apr, minimum_payment, start_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (loan.name, loan.principal, loan.apr, loan.minimum_payment, loan.start_date.isoformat()),
            )
            loan_id = cursor.lastrowid
        return Loan(
            id=loan_id,
            name=loan.name,
            principal=loan.principal,
            apr=loan.apr,
            minimum_payment=loan.minimum_payment,
            start_date=loan.start_date,
        )

    def list_all(self) -> list[Loan]:
        with self.db._connect() as conn:
            rows = conn.execute("SELECT * FROM loans ORDER BY created_at DESC").fetchall()
        return [
            Loan(
                id=row["id"],
                name=row["name"],
                principal=row["principal"],
                apr=row["apr"],
                minimum_payment=row["minimum_payment"],
                start_date=date.fromisoformat(row["start_date"]),
            )
            for row in rows
        ]

    def get(self, loan_id: int) -> Loan | None:
        with self.db._connect() as conn:
            row = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
        if not row:
            return None
        return Loan(
            id=row["id"],
            name=row["name"],
            principal=row["principal"],
            apr=row["apr"],
            minimum_payment=row["minimum_payment"],
            start_date=date.fromisoformat(row["start_date"]),
        )

    def delete(self, loan_id: int) -> bool:
        with self.db._connect() as conn:
            cursor = conn.execute("DELETE FROM loans WHERE id = ?", (loan_id,))
            return cursor.rowcount > 0

    def update(self, loan: Loan) -> Loan | None:
        if loan.id is None:
            return None
        with self.db._connect() as conn:
            conn.execute(
                """
                UPDATE loans
                SET name = ?, principal = ?, apr = ?, minimum_payment = ?, start_date = ?
                WHERE id = ?
                """,
                (loan.name, loan.principal, loan.apr, loan.minimum_payment, loan.start_date.isoformat(), loan.id),
            )
        return loan


class PaymentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, payment: Payment) -> Payment:
        with self.db._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO payments (loan_id, amount, payment_date, note)
                VALUES (?, ?, ?, ?)
                """,
                (payment.loan_id, payment.amount, payment.payment_date.isoformat(), payment.note),
            )
            payment_id = cursor.lastrowid
        return Payment(
            id=payment_id,
            loan_id=payment.loan_id,
            amount=payment.amount,
            payment_date=payment.payment_date,
            note=payment.note,
        )

    def list_for_loan(self, loan_id: int) -> list[Payment]:
        with self.db._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM payments
                WHERE loan_id = ?
                ORDER BY payment_date ASC
                """,
                (loan_id,),
            ).fetchall()
        return [
            Payment(
                id=row["id"],
                loan_id=row["loan_id"],
                amount=row["amount"],
                payment_date=date.fromisoformat(row["payment_date"]),
                note=row["note"],
            )
            for row in rows
        ]

    def get(self, payment_id: int) -> Payment | None:
        with self.db._connect() as conn:
            row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
        if not row:
            return None
        return Payment(
            id=row["id"],
            loan_id=row["loan_id"],
            amount=row["amount"],
            payment_date=date.fromisoformat(row["payment_date"]),
            note=row["note"],
        )

    def update(self, payment: Payment) -> Payment | None:
        if payment.id is None:
            return None
        with self.db._connect() as conn:
            conn.execute(
                """
                UPDATE payments
                SET amount = ?, payment_date = ?, note = ?
                WHERE id = ?
                """,
                (payment.amount, payment.payment_date.isoformat(), payment.note, payment.id),
            )
        return payment

    def delete(self, payment_id: int) -> bool:
        with self.db._connect() as conn:
            cursor = conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
            return cursor.rowcount > 0


class ScenarioRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, scenario: Scenario) -> Scenario:
        with self.db._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO scenarios (loan_id, name, extra_monthly)
                VALUES (?, ?, ?)
                """,
                (scenario.loan_id, scenario.name, scenario.extra_monthly),
            )
            scenario_id = cursor.lastrowid
        return Scenario(
            id=scenario_id,
            loan_id=scenario.loan_id,
            name=scenario.name,
            extra_monthly=scenario.extra_monthly,
        )

    def list_for_loan(self, loan_id: int) -> list[Scenario]:
        with self.db._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM scenarios
                WHERE loan_id = ?
                ORDER BY created_at DESC
                """,
                (loan_id,),
            ).fetchall()
        return [
            Scenario(
                id=row["id"],
                loan_id=row["loan_id"],
                name=row["name"],
                extra_monthly=row["extra_monthly"],
            )
            for row in rows
        ]

