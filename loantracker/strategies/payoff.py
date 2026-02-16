from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

from ..models import Loan, Payment


@dataclass(frozen=True)
class PayoffPoint:
    point_date: date
    balance: float


@dataclass(frozen=True)
class ProjectionSummary:
    points: list[PayoffPoint]
    total_interest: float
    total_paid: float
    payoff_date: date | None


class PayoffStrategy(Protocol):
    def current_balance(self, loan: Loan, payments: list[Payment]) -> float: ...

    def project(
        self,
        loan: Loan,
        payments: list[Payment],
        extra_monthly: float,
        granularity: str,
    ) -> list[PayoffPoint]: ...


class DailyPayoffStrategy:
    def project(
        self,
        loan: Loan,
        payments: list[Payment],
        extra_monthly: float,
        granularity: str,
    ) -> list[PayoffPoint]:
        daily_points = self._project_daily(loan, payments, extra_monthly)
        if granularity == "daily":
            return daily_points
        if granularity == "monthly":
            return _resample_monthly(daily_points)
        if granularity == "yearly":
            return _resample_yearly(daily_points)
        raise ValueError("Unsupported granularity")

    def current_balance(self, loan: Loan, payments: list[Payment]) -> float:
        """Compute the true current balance by replaying history from loan start."""
        today = date.today()
        if loan.start_date >= today:
            return loan.principal

        balance = loan.principal
        daily_rate = (loan.apr / 100.0) / 365.0

        # Build map of extra payments by date
        payment_map: dict[date, float] = {}
        for payment in payments:
            if payment.payment_date <= today:
                payment_map.setdefault(payment.payment_date, 0.0)
                payment_map[payment.payment_date] += payment.amount

        current_date = loan.start_date
        last_month_paid = (current_date.year, current_date.month)

        while current_date < today:
            current_date += timedelta(days=1)
            balance *= 1 + daily_rate

            current_month = (current_date.year, current_date.month)
            if current_month != last_month_paid:
                payment = min(loan.minimum_payment, balance)
                balance -= payment
                last_month_paid = current_month

            extra = payment_map.get(current_date, 0.0)
            if extra > 0:
                extra = min(extra, balance)
                balance -= extra

            balance = max(balance, 0.0)
            if balance <= 0:
                return 0.0

        return round(balance, 2)

    def project_with_summary(
        self,
        loan: Loan,
        payments: list[Payment],
        extra_monthly: float,
        granularity: str,
    ) -> ProjectionSummary:
        """Project payoff and return summary with accurate interest totals."""
        today = date.today()
        balance = self.current_balance(loan, payments)

        if balance <= 0:
            points = [PayoffPoint(point_date=today, balance=0.0)]
            if granularity == "monthly":
                points = _resample_monthly(points)
            elif granularity == "yearly":
                points = _resample_yearly(points)
            return ProjectionSummary(points=points, total_interest=0.0, total_paid=0.0, payoff_date=today)

        daily_rate = (loan.apr / 100.0) / 365.0
        max_days = 365 * 100

        payment_map: dict[date, float] = {}
        for payment in payments:
            if payment.payment_date > today:
                payment_map.setdefault(payment.payment_date, 0.0)
                payment_map[payment.payment_date] += payment.amount

        daily_points: list[PayoffPoint] = [PayoffPoint(point_date=today, balance=round(balance, 2))]
        current_date = today
        last_month_paid = (today.year, today.month)
        total_interest = 0.0
        total_paid = 0.0
        payoff_date: date | None = None

        for _ in range(max_days):
            current_date += timedelta(days=1)

            daily_interest = balance * daily_rate
            balance += daily_interest
            total_interest += daily_interest

            current_month = (current_date.year, current_date.month)
            if current_month != last_month_paid:
                month_payment = loan.minimum_payment + extra_monthly
                month_payment = min(month_payment, balance)
                balance -= month_payment
                total_paid += month_payment
                last_month_paid = current_month

            extra = payment_map.get(current_date, 0.0)
            if extra > 0:
                extra = min(extra, balance)
                balance -= extra
                total_paid += extra

            balance = max(balance, 0.0)
            daily_points.append(PayoffPoint(point_date=current_date, balance=round(balance, 2)))

            if balance <= 0:
                payoff_date = current_date
                break
        else:
            raise ValueError("Projection exceeded 100 years; check payment amount")

        if granularity == "daily":
            points = daily_points
        elif granularity == "monthly":
            points = _resample_monthly(daily_points)
        elif granularity == "yearly":
            points = _resample_yearly(daily_points)
        else:
            raise ValueError("Unsupported granularity")

        return ProjectionSummary(
            points=points,
            total_interest=round(total_interest, 2),
            total_paid=round(total_paid, 2),
            payoff_date=payoff_date,
        )

    def _project_daily(self, loan: Loan, payments: list[Payment], extra_monthly: float) -> list[PayoffPoint]:
        today = date.today()

        balance = self.current_balance(loan, payments)

        if balance <= 0:
            return [PayoffPoint(point_date=today, balance=0.0)]

        daily_rate = (loan.apr / 100.0) / 365.0
        max_days = 365 * 100

        # Build payment map from future extra payments only
        payment_map: dict[date, float] = {}
        for payment in payments:
            if payment.payment_date > today:
                payment_map.setdefault(payment.payment_date, 0.0)
                payment_map[payment.payment_date] += payment.amount

        points: list[PayoffPoint] = [PayoffPoint(point_date=today, balance=round(balance, 2))]
        current_date = today
        last_month_paid = (today.year, today.month)

        for _ in range(max_days):
            current_date += timedelta(days=1)

            # Accrue daily interest
            balance *= 1 + daily_rate

            # Check if we should make monthly payment (once per month)
            current_month = (current_date.year, current_date.month)
            if current_month != last_month_paid:
                total_payment = loan.minimum_payment + extra_monthly
                total_payment = min(total_payment, balance)
                balance -= total_payment
                last_month_paid = current_month

            # Apply any extra one-time payments on this date
            extra = payment_map.get(current_date, 0.0)
            if extra > 0:
                extra = min(extra, balance)
                balance -= extra

            balance = max(balance, 0.0)
            points.append(PayoffPoint(point_date=current_date, balance=round(balance, 2)))

            if balance <= 0:
                break
        else:
            raise ValueError("Projection exceeded 100 years; check payment amount")

        return points


def _resample_monthly(points: list[PayoffPoint]) -> list[PayoffPoint]:
    if not points:
        return points
    sampled: list[PayoffPoint] = []
    current_month = (points[0].point_date.year, points[0].point_date.month)
    last_point = points[0]
    for point in points:
        month_key = (point.point_date.year, point.point_date.month)
        if month_key != current_month:
            sampled.append(last_point)
            current_month = month_key
        last_point = point
    sampled.append(last_point)
    return sampled


def _resample_yearly(points: list[PayoffPoint]) -> list[PayoffPoint]:
    if not points:
        return points
    sampled: list[PayoffPoint] = []
    current_year = points[0].point_date.year
    last_point = points[0]
    for point in points:
        if point.point_date.year != current_year:
            sampled.append(last_point)
            current_year = point.point_date.year
        last_point = point
    sampled.append(last_point)
    return sampled

