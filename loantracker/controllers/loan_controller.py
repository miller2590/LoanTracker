from __future__ import annotations

from datetime import date

from ..db import LoanRepository
from ..models import Loan
from ..validation import validate_loan


class LoanController:
    def __init__(self, repo: LoanRepository) -> None:
        self.repo = repo

    def create(self, name: str, principal: float, apr: float, minimum_payment: float, start_date: date) -> Loan:
        validate_loan(name, principal, apr, minimum_payment, start_date)
        return self.repo.create(
            Loan(
                id=None,
                name=name.strip(),
                principal=principal,
                apr=apr,
                minimum_payment=minimum_payment,
                start_date=start_date,
            )
        )

    def list_all(self) -> list[Loan]:
        return self.repo.list_all()

    def get(self, loan_id: int) -> Loan | None:
        return self.repo.get(loan_id)

    def delete(self, loan_id: int) -> bool:
        return self.repo.delete(loan_id)

    def update(self, loan_id: int, name: str, principal: float, apr: float, minimum_payment: float, start_date: date) -> Loan | None:
        validate_loan(name, principal, apr, minimum_payment, start_date)
        loan = Loan(
            id=loan_id,
            name=name.strip(),
            principal=principal,
            apr=apr,
            minimum_payment=minimum_payment,
            start_date=start_date,
        )
        return self.repo.update(loan)

