"""Integration tests for database repositories using in-memory SQLite."""

from __future__ import annotations

import pytest
from datetime import date

from loantracker.db import Database, LoanRepository, PaymentRepository, ScenarioRepository
from loantracker.models import Loan, Payment, Scenario


@pytest.fixture
def db(tmp_path) -> Database:
    """Create a database with a temporary file."""
    db = Database(tmp_path / "test.db")
    db.init()
    return db


@pytest.fixture
def loan_repo(db: Database) -> LoanRepository:
    return LoanRepository(db)


@pytest.fixture
def payment_repo(db: Database) -> PaymentRepository:
    return PaymentRepository(db)


@pytest.fixture
def scenario_repo(db: Database) -> ScenarioRepository:
    return ScenarioRepository(db)


@pytest.fixture
def sample_loan(loan_repo: LoanRepository) -> Loan:
    """Create and return a persisted sample loan."""
    return loan_repo.create(
        Loan(id=None, name="Test Loan", principal=100000.0, apr=6.5, minimum_payment=632.07, start_date=date(2025, 1, 1))
    )


class TestDatabase:
    """Tests for Database class."""

    def test_init_creates_tables(self, db: Database) -> None:
        with db.connect() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        table_names = [t["name"] for t in tables]
        assert "loans" in table_names
        assert "payments" in table_names
        assert "scenarios" in table_names

    def test_init_is_idempotent(self, db: Database) -> None:
        db.init()  # second call should not raise
        with db.connect() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        assert len(tables) >= 3

    def test_foreign_keys_enabled(self, db: Database) -> None:
        with db.connect() as conn:
            result = conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1

    def test_rollback_on_error(self, db: Database, loan_repo: LoanRepository) -> None:
        loan_repo.create(
            Loan(id=None, name="Rollback Test", principal=50000.0, apr=5.0, minimum_payment=300.0, start_date=date.today())
        )
        try:
            with db.connect() as conn:
                conn.execute("INSERT INTO loans (name, principal, apr, minimum_payment, start_date) VALUES (?, ?, ?, ?, ?)",
                    ("Bad", 1.0, 1.0, 1.0, "2025-01-01"))
                raise RuntimeError("force rollback")
        except RuntimeError:
            pass
        loans = loan_repo.list_all()
        assert len(loans) == 1
        assert loans[0].name == "Rollback Test"


class TestLoanRepository:
    """Tests for LoanRepository."""

    def test_create_and_get(self, loan_repo: LoanRepository) -> None:
        loan = loan_repo.create(
            Loan(id=None, name="Car Loan", principal=25000.0, apr=4.5, minimum_payment=450.0, start_date=date(2025, 6, 1))
        )
        assert loan.id is not None
        fetched = loan_repo.get(loan.id)
        assert fetched is not None
        assert fetched.name == "Car Loan"
        assert fetched.principal == 25000.0

    def test_list_all(self, loan_repo: LoanRepository) -> None:
        loan_repo.create(Loan(id=None, name="Loan A", principal=10000.0, apr=5.0, minimum_payment=200.0, start_date=date.today()))
        loan_repo.create(Loan(id=None, name="Loan B", principal=20000.0, apr=6.0, minimum_payment=400.0, start_date=date.today()))
        loans = loan_repo.list_all()
        assert len(loans) == 2

    def test_update(self, loan_repo: LoanRepository) -> None:
        loan = loan_repo.create(
            Loan(id=None, name="Original", principal=10000.0, apr=5.0, minimum_payment=200.0, start_date=date.today())
        )
        updated = loan_repo.update(
            Loan(id=loan.id, name="Updated", principal=15000.0, apr=5.5, minimum_payment=250.0, start_date=date.today())
        )
        assert updated is not None
        fetched = loan_repo.get(loan.id)
        assert fetched.name == "Updated"
        assert fetched.principal == 15000.0

    def test_update_without_id_returns_none(self, loan_repo: LoanRepository) -> None:
        result = loan_repo.update(
            Loan(id=None, name="No ID", principal=10000.0, apr=5.0, minimum_payment=200.0, start_date=date.today())
        )
        assert result is None

    def test_delete(self, loan_repo: LoanRepository) -> None:
        loan = loan_repo.create(
            Loan(id=None, name="Delete Me", principal=10000.0, apr=5.0, minimum_payment=200.0, start_date=date.today())
        )
        assert loan_repo.delete(loan.id) is True
        assert loan_repo.get(loan.id) is None

    def test_delete_nonexistent(self, loan_repo: LoanRepository) -> None:
        assert loan_repo.delete(999) is False

    def test_get_nonexistent(self, loan_repo: LoanRepository) -> None:
        assert loan_repo.get(999) is None

    def test_cascade_delete_payments(self, loan_repo: LoanRepository, payment_repo: PaymentRepository) -> None:
        loan = loan_repo.create(
            Loan(id=None, name="Cascade", principal=10000.0, apr=5.0, minimum_payment=200.0, start_date=date.today())
        )
        payment_repo.create(Payment(id=None, loan_id=loan.id, amount=500.0, payment_date=date.today(), note=None))
        loan_repo.delete(loan.id)
        assert payment_repo.list_for_loan(loan.id) == []

    def test_cascade_delete_scenarios(self, loan_repo: LoanRepository, scenario_repo: ScenarioRepository) -> None:
        loan = loan_repo.create(
            Loan(id=None, name="Cascade", principal=10000.0, apr=5.0, minimum_payment=200.0, start_date=date.today())
        )
        scenario_repo.create(Scenario(id=None, loan_id=loan.id, name="Test", extra_monthly=100.0))
        loan_repo.delete(loan.id)
        assert scenario_repo.list_for_loan(loan.id) == []


class TestPaymentRepository:
    """Tests for PaymentRepository."""

    def test_create_and_get(self, payment_repo: PaymentRepository, sample_loan: Loan) -> None:
        payment = payment_repo.create(
            Payment(id=None, loan_id=sample_loan.id, amount=500.0, payment_date=date(2025, 3, 1), note="Extra")
        )
        assert payment.id is not None
        fetched = payment_repo.get(payment.id)
        assert fetched is not None
        assert fetched.amount == 500.0
        assert fetched.note == "Extra"

    def test_list_for_loan_ordered_by_date(self, payment_repo: PaymentRepository, sample_loan: Loan) -> None:
        payment_repo.create(Payment(id=None, loan_id=sample_loan.id, amount=200.0, payment_date=date(2025, 3, 1), note=None))
        payment_repo.create(Payment(id=None, loan_id=sample_loan.id, amount=300.0, payment_date=date(2025, 1, 1), note=None))
        payments = payment_repo.list_for_loan(sample_loan.id)
        assert len(payments) == 2
        assert payments[0].payment_date < payments[1].payment_date

    def test_update(self, payment_repo: PaymentRepository, sample_loan: Loan) -> None:
        payment = payment_repo.create(
            Payment(id=None, loan_id=sample_loan.id, amount=500.0, payment_date=date.today(), note="Old")
        )
        updated = payment_repo.update(
            Payment(id=payment.id, loan_id=sample_loan.id, amount=750.0, payment_date=date.today(), note="New")
        )
        assert updated is not None
        fetched = payment_repo.get(payment.id)
        assert fetched.amount == 750.0
        assert fetched.note == "New"

    def test_update_without_id_returns_none(self, payment_repo: PaymentRepository, sample_loan: Loan) -> None:
        result = payment_repo.update(
            Payment(id=None, loan_id=sample_loan.id, amount=500.0, payment_date=date.today(), note=None)
        )
        assert result is None

    def test_delete(self, payment_repo: PaymentRepository, sample_loan: Loan) -> None:
        payment = payment_repo.create(
            Payment(id=None, loan_id=sample_loan.id, amount=500.0, payment_date=date.today(), note=None)
        )
        assert payment_repo.delete(payment.id) is True
        assert payment_repo.get(payment.id) is None

    def test_delete_nonexistent(self, payment_repo: PaymentRepository) -> None:
        assert payment_repo.delete(999) is False

    def test_get_nonexistent(self, payment_repo: PaymentRepository) -> None:
        assert payment_repo.get(999) is None


class TestScenarioRepository:
    """Tests for ScenarioRepository."""

    def test_create_and_list(self, scenario_repo: ScenarioRepository, sample_loan: Loan) -> None:
        scenario = scenario_repo.create(
            Scenario(id=None, loan_id=sample_loan.id, name="Aggressive", extra_monthly=500.0)
        )
        assert scenario.id is not None
        scenarios = scenario_repo.list_for_loan(sample_loan.id)
        assert len(scenarios) == 1
        assert scenarios[0].name == "Aggressive"

    def test_delete(self, scenario_repo: ScenarioRepository, sample_loan: Loan) -> None:
        scenario = scenario_repo.create(
            Scenario(id=None, loan_id=sample_loan.id, name="Delete Me", extra_monthly=100.0)
        )
        assert scenario_repo.delete(scenario.id) is True
        assert scenario_repo.list_for_loan(sample_loan.id) == []

    def test_delete_nonexistent(self, scenario_repo: ScenarioRepository) -> None:
        assert scenario_repo.delete(999) is False

    def test_list_for_loan_empty(self, scenario_repo: ScenarioRepository, sample_loan: Loan) -> None:
        assert scenario_repo.list_for_loan(sample_loan.id) == []
