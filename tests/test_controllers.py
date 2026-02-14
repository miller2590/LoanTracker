"""Tests for controllers."""

from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import MagicMock, Mock

from loantracker.controllers import LoanController, PaymentController
from loantracker.models import Loan, Payment


class TestLoanController:
    """Tests for LoanController."""

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        """Create a mock loan repository."""
        return MagicMock()

    @pytest.fixture
    def controller(self, mock_repo: MagicMock) -> LoanController:
        """Create a controller with mock repository."""
        return LoanController(mock_repo)

    def test_create_loan(self, controller: LoanController, mock_repo: MagicMock) -> None:
        """Test creating a new loan."""
        expected_loan = Loan(
            id=1,
            name="Test",
            principal=100000.0,
            apr=6.5,
            minimum_payment=632.07,
            start_date=date.today(),
        )
        mock_repo.create.return_value = expected_loan

        loan = controller.create("Test", 100000.0, 6.5, 632.07, date.today())

        assert loan == expected_loan
        mock_repo.create.assert_called_once()

    def test_create_loan_validates_name(self, controller: LoanController) -> None:
        """Test that create validates loan name."""
        with pytest.raises(ValueError, match="name"):
            controller.create("", 100000.0, 6.5, 632.07, date.today())

    def test_create_loan_validates_principal(self, controller: LoanController) -> None:
        """Test that create validates principal."""
        with pytest.raises(ValueError, match="[Pp]rincipal"):
            controller.create("Test", 0, 6.5, 632.07, date.today())

        with pytest.raises(ValueError, match="[Pp]rincipal"):
            controller.create("Test", -100, 6.5, 632.07, date.today())

    def test_create_loan_validates_apr(self, controller: LoanController) -> None:
        """Test that create validates APR."""
        with pytest.raises(ValueError, match="APR"):
            controller.create("Test", 100000.0, -1, 632.07, date.today())

        with pytest.raises(ValueError, match="APR"):
            controller.create("Test", 100000.0, 101, 632.07, date.today())

    def test_get_loan(self, controller: LoanController, mock_repo: MagicMock) -> None:
        """Test getting a loan by ID."""
        expected = Loan(
            id=1,
            name="Test",
            principal=100000.0,
            apr=6.5,
            minimum_payment=632.07,
            start_date=date.today(),
        )
        mock_repo.get.return_value = expected

        result = controller.get(1)

        assert result == expected
        mock_repo.get.assert_called_once_with(1)

    def test_list_all_loans(self, controller: LoanController, mock_repo: MagicMock) -> None:
        """Test listing all loans."""
        expected = [
            Loan(id=1, name="Loan 1", principal=100000.0, apr=6.5, minimum_payment=632.07, start_date=date.today()),
            Loan(id=2, name="Loan 2", principal=50000.0, apr=5.0, minimum_payment=300.0, start_date=date.today()),
        ]
        mock_repo.list_all.return_value = expected

        result = controller.list_all()

        assert result == expected

    def test_delete_loan(self, controller: LoanController, mock_repo: MagicMock) -> None:
        """Test deleting a loan."""
        mock_repo.delete.return_value = True

        result = controller.delete(1)

        assert result is True
        mock_repo.delete.assert_called_once_with(1)


class TestPaymentController:
    """Tests for PaymentController."""

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        """Create a mock payment repository."""
        return MagicMock()

    @pytest.fixture
    def controller(self, mock_repo: MagicMock) -> PaymentController:
        """Create a controller with mock repository."""
        return PaymentController(mock_repo)

    def test_create_payment(self, controller: PaymentController, mock_repo: MagicMock) -> None:
        """Test creating a new payment."""
        expected_payment = Payment(
            id=1,
            loan_id=1,
            amount=500.0,
            payment_date=date.today(),
            note="Test",
        )
        mock_repo.create.return_value = expected_payment

        payment = controller.create(1, 500.0, date.today(), "Test")

        assert payment == expected_payment
        mock_repo.create.assert_called_once()

    def test_create_payment_validates_amount(self, controller: PaymentController) -> None:
        """Test that create validates amount."""
        with pytest.raises(ValueError, match="[Aa]mount"):
            controller.create(1, 0, date.today(), "")

        with pytest.raises(ValueError, match="[Aa]mount"):
            controller.create(1, -100, date.today(), "")

    def test_list_payments_for_loan(self, controller: PaymentController, mock_repo: MagicMock) -> None:
        """Test listing payments for a loan."""
        expected = [
            Payment(id=1, loan_id=1, amount=500.0, payment_date=date.today(), note="Test"),
        ]
        mock_repo.list_for_loan.return_value = expected

        result = controller.list_for_loan(1)

        assert result == expected
        mock_repo.list_for_loan.assert_called_once_with(1)

