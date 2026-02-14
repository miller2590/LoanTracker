from __future__ import annotations

from datetime import date

from ..db import PaymentRepository
from ..models import Payment
from ..validation import validate_payment


class PaymentController:
    def __init__(self, repo: PaymentRepository) -> None:
        self.repo = repo

    def create(self, loan_id: int, amount: float, payment_date: date, note: str | None) -> Payment:
        validate_payment(amount, payment_date)
        return self.repo.create(
            Payment(
                id=None,
                loan_id=loan_id,
                amount=amount,
                payment_date=payment_date,
                note=note.strip() if note else None,
            )
        )

    def list_for_loan(self, loan_id: int) -> list[Payment]:
        return self.repo.list_for_loan(loan_id)

    def get(self, payment_id: int) -> Payment | None:
        return self.repo.get(payment_id)

    def update(self, payment_id: int, amount: float, payment_date: date, note: str | None) -> Payment | None:
        validate_payment(amount, payment_date)
        existing = self.repo.get(payment_id)
        if not existing:
            return None
        updated = Payment(
            id=payment_id,
            loan_id=existing.loan_id,
            amount=amount,
            payment_date=payment_date,
            note=note.strip() if note else None,
        )
        return self.repo.update(updated)

    def delete(self, payment_id: int) -> bool:
        return self.repo.delete(payment_id)

