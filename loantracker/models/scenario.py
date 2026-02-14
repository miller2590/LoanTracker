from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    id: int | None
    loan_id: int
    name: str
    extra_monthly: float

