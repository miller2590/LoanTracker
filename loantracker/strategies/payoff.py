from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

from ..models import Loan, Payment


@dataclass(frozen=True)
class PayoffPoint:
    point_date: date
    balance: float


class PayoffStrategy(Protocol):
    def project(
        self,
        loan: Loan,
        payments: list[Payment],
        extra_monthly: float,
        granularity: str,
    ) -> list[PayoffPoint]:
        ...


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

    def _project_daily(self, loan: Loan, payments: list[Payment], extra_monthly: float) -> list[PayoffPoint]:
        from datetime import date as date_type
        today = date_type.today()

        # Calculate current balance by subtracting past extra payments from principal
        past_payments_total = sum(p.amount for p in payments if p.payment_date <= today)
        balance = loan.principal - past_payments_total

        # If balance is already paid off, return empty projection
        if balance <= 0:
            return [PayoffPoint(point_date=today, balance=0.0)]

        daily_rate = (loan.apr / 100.0) / 365.0
        start_date = today
        max_days = 365 * 100

        # Build payment map from future extra payments only
        payment_map: dict[date, float] = {}
        for payment in payments:
            if payment.payment_date > today:
                payment_map.setdefault(payment.payment_date, 0.0)
                payment_map[payment.payment_date] += payment.amount

        points: list[PayoffPoint] = [PayoffPoint(point_date=start_date, balance=round(balance, 2))]
        current_date = start_date
        last_month_paid = (start_date.year, start_date.month)

        for _ in range(max_days):
            current_date += timedelta(days=1)

            # Accrue daily interest
            balance *= 1 + daily_rate

            # Check if we should make monthly payment (once per month)
            current_month = (current_date.year, current_date.month)
            if current_month != last_month_paid:
                # Make the scheduled monthly payment
                total_payment = loan.minimum_payment + extra_monthly
                total_payment = min(total_payment, balance)
                balance -= total_payment
                last_month_paid = current_month

            # Apply any extra one-time payments on this date
            extra_payment = payment_map.get(current_date, 0.0)
            if extra_payment > 0:
                extra_payment = min(extra_payment, balance)
                balance -= extra_payment

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

