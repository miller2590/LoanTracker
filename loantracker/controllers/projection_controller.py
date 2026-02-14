from __future__ import annotations

from ..db import LoanRepository, PaymentRepository
from ..strategies import DailyPayoffStrategy, PayoffPoint


class ProjectionController:
    def __init__(self, strategy: DailyPayoffStrategy, payments_repo: PaymentRepository, loans_repo: LoanRepository) -> None:
        self.strategy = strategy
        self.payments_repo = payments_repo
        self.loans_repo = loans_repo

    def project(self, loan_id: int, extra_monthly: float, granularity: str) -> list[PayoffPoint]:
        loan = self.loans_repo.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        payments = self.payments_repo.list_for_loan(loan_id)
        return self.strategy.project(loan, payments, extra_monthly, granularity)

