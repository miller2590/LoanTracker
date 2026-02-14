"""Tests for payoff strategy calculations."""

from __future__ import annotations

import pytest
from datetime import date

from loantracker.models import Loan, Payment
from loantracker.strategies import DailyPayoffStrategy, PayoffPoint


@pytest.fixture
def sample_loan() -> Loan:
    """Create a sample loan for testing."""
    return Loan(
        id=1,
        name="Test Loan",
        principal=100000.0,
        apr=6.5,
        minimum_payment=632.07,
        start_date=date(2025, 10, 30),
    )


@pytest.fixture
def strategy() -> DailyPayoffStrategy:
    """Create a payoff strategy instance."""
    return DailyPayoffStrategy()


class TestDailyPayoffStrategy:
    """Tests for DailyPayoffStrategy."""

    def test_project_returns_points(self, strategy: DailyPayoffStrategy, sample_loan: Loan) -> None:
        """Test that projection returns a list of points."""
        points = strategy.project(sample_loan, [], extra_monthly=0.0, granularity="monthly")

        assert len(points) > 0
        assert all(isinstance(p, PayoffPoint) for p in points)

    def test_project_ends_at_zero_balance(self, strategy: DailyPayoffStrategy, sample_loan: Loan) -> None:
        """Test that projection ends when balance reaches zero."""
        points = strategy.project(sample_loan, [], extra_monthly=0.0, granularity="monthly")

        assert points[-1].balance == 0.0

    def test_extra_payment_reduces_payoff_time(self, strategy: DailyPayoffStrategy, sample_loan: Loan) -> None:
        """Test that extra payments reduce the payoff time."""
        baseline = strategy.project(sample_loan, [], extra_monthly=0.0, granularity="monthly")
        with_extra = strategy.project(sample_loan, [], extra_monthly=200.0, granularity="monthly")

        assert len(with_extra) < len(baseline)

    def test_extra_payment_reduces_total_interest(self, strategy: DailyPayoffStrategy, sample_loan: Loan) -> None:
        """Test that extra payments reduce total interest paid."""
        baseline = strategy.project(sample_loan, [], extra_monthly=0.0, granularity="monthly")
        with_extra = strategy.project(sample_loan, [], extra_monthly=200.0, granularity="monthly")

        # Calculate approximate total interest (total payments - principal)
        baseline_total = len(baseline) * sample_loan.minimum_payment
        with_extra_total = len(with_extra) * (sample_loan.minimum_payment + 200.0)

        baseline_interest = baseline_total - sample_loan.principal
        with_extra_interest = with_extra_total - sample_loan.principal

        assert with_extra_interest < baseline_interest

    def test_granularity_monthly(self, strategy: DailyPayoffStrategy, sample_loan: Loan) -> None:
        """Test monthly granularity returns fewer points than daily would."""
        points = strategy.project(sample_loan, [], extra_monthly=0.0, granularity="monthly")

        # Monthly should have roughly 12 points per year
        years_to_payoff = len(points) / 12
        assert 10 < years_to_payoff < 40  # Reasonable range for a 30-year mortgage

    def test_granularity_yearly(self, strategy: DailyPayoffStrategy, sample_loan: Loan) -> None:
        """Test yearly granularity returns one point per year."""
        points = strategy.project(sample_loan, [], extra_monthly=0.0, granularity="yearly")

        # Should be roughly number of years to payoff
        assert 10 < len(points) < 40

    def test_past_payments_reduce_balance(self, strategy: DailyPayoffStrategy, sample_loan: Loan) -> None:
        """Test that past extra payments reduce the starting balance."""
        past_payment = Payment(
            id=1,
            loan_id=1,
            amount=5000.0,
            payment_date=date.today(),
            note="Extra payment",
        )

        baseline = strategy.project(sample_loan, [], extra_monthly=0.0, granularity="monthly")
        with_payment = strategy.project(sample_loan, [past_payment], extra_monthly=0.0, granularity="monthly")

        # With a $5000 extra payment, should have fewer months
        assert len(with_payment) < len(baseline)

    def test_invalid_granularity_raises_error(self, strategy: DailyPayoffStrategy, sample_loan: Loan) -> None:
        """Test that invalid granularity raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported granularity"):
            strategy.project(sample_loan, [], extra_monthly=0.0, granularity="weekly")


class TestPayoffPoint:
    """Tests for PayoffPoint dataclass."""

    def test_payoff_point_is_frozen(self) -> None:
        """Test that PayoffPoint is immutable."""
        point = PayoffPoint(point_date=date.today(), balance=1000.0)

        with pytest.raises(AttributeError):
            point.balance = 500.0

    def test_payoff_point_equality(self) -> None:
        """Test PayoffPoint equality comparison."""
        today = date.today()
        point1 = PayoffPoint(point_date=today, balance=1000.0)
        point2 = PayoffPoint(point_date=today, balance=1000.0)

        assert point1 == point2

