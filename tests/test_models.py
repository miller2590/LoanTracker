"""Tests for model classes."""

from __future__ import annotations

import pytest
from datetime import date

from loantracker.models import Loan, Payment, Scenario


class TestLoan:
    """Tests for Loan model."""

    def test_loan_creation(self) -> None:
        """Test creating a loan with all fields."""
        loan = Loan(
            id=1,
            name="Test Loan",
            principal=100000.0,
            apr=6.5,
            minimum_payment=632.07,
            start_date=date(2025, 1, 1),
        )

        assert loan.id == 1
        assert loan.name == "Test Loan"
        assert loan.principal == 100000.0
        assert loan.apr == 6.5
        assert loan.minimum_payment == 632.07
        assert loan.start_date == date(2025, 1, 1)

    def test_loan_without_id(self) -> None:
        """Test creating a loan without an ID (for new loans)."""
        loan = Loan(
            id=None,
            name="New Loan",
            principal=50000.0,
            apr=5.0,
            minimum_payment=300.0,
            start_date=date.today(),
        )

        assert loan.id is None


class TestPayment:
    """Tests for Payment model."""

    def test_payment_creation(self) -> None:
        """Test creating a payment with all fields."""
        payment = Payment(
            id=1,
            loan_id=1,
            amount=500.0,
            payment_date=date(2025, 2, 15),
            note="Extra payment",
        )

        assert payment.id == 1
        assert payment.loan_id == 1
        assert payment.amount == 500.0
        assert payment.payment_date == date(2025, 2, 15)
        assert payment.note == "Extra payment"

    def test_payment_without_note(self) -> None:
        """Test creating a payment without a note."""
        payment = Payment(
            id=1,
            loan_id=1,
            amount=500.0,
            payment_date=date.today(),
            note=None,
        )

        assert payment.note is None


class TestScenario:
    """Tests for Scenario model."""

    def test_scenario_creation(self) -> None:
        """Test creating a scenario."""
        scenario = Scenario(
            id=1,
            loan_id=1,
            name="Aggressive Payoff",
            extra_monthly=500.0,
        )

        assert scenario.id == 1
        assert scenario.loan_id == 1
        assert scenario.name == "Aggressive Payoff"
        assert scenario.extra_monthly == 500.0

