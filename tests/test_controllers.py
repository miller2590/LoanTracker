"""Tests for controllers."""

from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import MagicMock, Mock

from loantracker.controllers import LoanController, PaymentController, ScenarioController, ProjectionController
from loantracker.models import Loan, Payment, Scenario
from loantracker.strategies import DailyPayoffStrategy, PayoffPoint


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


class TestLoanControllerUpdate:
    """Tests for LoanController.update."""

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def controller(self, mock_repo: MagicMock) -> LoanController:
        return LoanController(mock_repo)

    def test_update_loan(self, controller: LoanController, mock_repo: MagicMock) -> None:
        """Test updating a loan."""
        updated_loan = Loan(id=1, name="Updated", principal=120000.0, apr=5.0, minimum_payment=700.0, start_date=date.today())
        mock_repo.update.return_value = updated_loan

        result = controller.update(1, "Updated", 120000.0, 5.0, 700.0, date.today())

        assert result == updated_loan
        mock_repo.update.assert_called_once()

    def test_update_validates_name(self, controller: LoanController) -> None:
        """Test that update validates loan name."""
        with pytest.raises(ValueError, match="name"):
            controller.update(1, "", 100000.0, 6.5, 632.07, date.today())

    def test_update_validates_principal(self, controller: LoanController) -> None:
        """Test that update validates principal."""
        with pytest.raises(ValueError, match="[Pp]rincipal"):
            controller.update(1, "Test", 0, 6.5, 632.07, date.today())

    def test_update_validates_apr(self, controller: LoanController) -> None:
        """Test that update validates APR."""
        with pytest.raises(ValueError, match="APR"):
            controller.update(1, "Test", 100000.0, -1, 632.07, date.today())


class TestScenarioController:
    """Tests for ScenarioController."""

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def controller(self, mock_repo: MagicMock) -> ScenarioController:
        return ScenarioController(mock_repo)

    def test_save_scenario(self, controller: ScenarioController, mock_repo: MagicMock) -> None:
        """Test saving a scenario."""
        expected = Scenario(id=1, loan_id=1, name="Aggressive", extra_monthly=500.0)
        mock_repo.create.return_value = expected

        result = controller.save(1, "Aggressive", 500.0)

        assert result == expected
        mock_repo.create.assert_called_once()

    def test_save_validates_name(self, controller: ScenarioController) -> None:
        """Test that save validates scenario name."""
        with pytest.raises(ValueError, match="name"):
            controller.save(1, "", 500.0)

    def test_save_validates_extra_monthly(self, controller: ScenarioController) -> None:
        """Test that save validates extra monthly amount."""
        with pytest.raises(ValueError, match="[Ee]xtra"):
            controller.save(1, "Test", -100.0)

    def test_list_for_loan(self, controller: ScenarioController, mock_repo: MagicMock) -> None:
        """Test listing scenarios for a loan."""
        expected = [Scenario(id=1, loan_id=1, name="Test", extra_monthly=100.0)]
        mock_repo.list_for_loan.return_value = expected

        result = controller.list_for_loan(1)

        assert result == expected
        mock_repo.list_for_loan.assert_called_once_with(1)

    def test_delete_scenario(self, controller: ScenarioController, mock_repo: MagicMock) -> None:
        """Test deleting a scenario."""
        mock_repo.delete.return_value = True

        result = controller.delete(1)

        assert result is True
        mock_repo.delete.assert_called_once_with(1)

    def test_save_allows_zero_extra(self, controller: ScenarioController, mock_repo: MagicMock) -> None:
        """Test that saving with 0 extra monthly is allowed."""
        expected = Scenario(id=1, loan_id=1, name="Baseline", extra_monthly=0.0)
        mock_repo.create.return_value = expected

        result = controller.save(1, "Baseline", 0.0)
        assert result == expected


class TestProjectionController:
    """Tests for ProjectionController."""

    @pytest.fixture
    def mock_loans_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_payments_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def strategy(self) -> DailyPayoffStrategy:
        return DailyPayoffStrategy()

    @pytest.fixture
    def controller(self, strategy, mock_payments_repo, mock_loans_repo) -> ProjectionController:
        return ProjectionController(strategy, mock_payments_repo, mock_loans_repo)

    def test_project_returns_points(self, controller, mock_loans_repo, mock_payments_repo) -> None:
        """Test that project returns payoff points."""
        loan = Loan(id=1, name="Test", principal=10000.0, apr=5.0, minimum_payment=500.0, start_date=date(2025, 1, 1))
        mock_loans_repo.get.return_value = loan
        mock_payments_repo.list_for_loan.return_value = []

        points = controller.project(1, 0.0, "monthly")

        assert len(points) > 0
        assert points[-1].balance == 0.0

    def test_project_loan_not_found(self, controller, mock_loans_repo) -> None:
        """Test that project raises when loan not found."""
        mock_loans_repo.get.return_value = None

        with pytest.raises(ValueError, match="Loan not found"):
            controller.project(999, 0.0, "monthly")

    def test_current_balance(self, controller, mock_loans_repo, mock_payments_repo) -> None:
        """Test current_balance returns a positive value for an active loan."""
        loan = Loan(id=1, name="Test", principal=100000.0, apr=6.5, minimum_payment=632.07, start_date=date(2025, 1, 1))
        mock_loans_repo.get.return_value = loan
        mock_payments_repo.list_for_loan.return_value = []

        balance = controller.current_balance(1)

        assert balance > 0
        # Balance should be less than principal (minimum payments made) or equal if start_date is today/future
        # Since start_date is in the past, payments reduce balance but interest increases it

    def test_current_balance_loan_not_found(self, controller, mock_loans_repo) -> None:
        """Test current_balance raises when loan not found."""
        mock_loans_repo.get.return_value = None

        with pytest.raises(ValueError, match="Loan not found"):
            controller.current_balance(999)

    def test_project_with_summary(self, controller, mock_loans_repo, mock_payments_repo) -> None:
        """Test project_with_summary returns accurate totals."""
        loan = Loan(id=1, name="Test", principal=10000.0, apr=5.0, minimum_payment=500.0, start_date=date(2025, 1, 1))
        mock_loans_repo.get.return_value = loan
        mock_payments_repo.list_for_loan.return_value = []

        summary = controller.project_with_summary(1, 0.0, "monthly")

        assert summary.total_interest > 0
        assert summary.total_paid > 0
        assert summary.payoff_date is not None
        assert len(summary.points) > 0
        assert summary.points[-1].balance == 0.0

