from __future__ import annotations

from ..db import LoanRepository, PaymentRepository
from ..strategies import DailyPayoffStrategy, PayoffPoint, ProjectionSummary


class ProjectionController:
    def __init__(self, strategy: DailyPayoffStrategy, payments_repo: PaymentRepository, loans_repo: LoanRepository) -> None:
        self.strategy = strategy
        self.payments_repo = payments_repo
        self.loans_repo = loans_repo

    def current_balance(self, loan_id: int) -> float:
        loan = self.loans_repo.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        payments = self.payments_repo.list_for_loan(loan_id)
        return self.strategy.current_balance(loan, payments)

    def project(self, loan_id: int, extra_monthly: float, granularity: str) -> list[PayoffPoint]:
        loan = self.loans_repo.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        payments = self.payments_repo.list_for_loan(loan_id)
        return self.strategy.project(loan, payments, extra_monthly, granularity)

    def project_with_summary(self, loan_id: int, extra_monthly: float, granularity: str) -> ProjectionSummary:
        loan = self.loans_repo.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        payments = self.payments_repo.list_for_loan(loan_id)
        return self.strategy.project_with_summary(loan, payments, extra_monthly, granularity)

