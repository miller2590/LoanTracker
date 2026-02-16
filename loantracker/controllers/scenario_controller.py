from __future__ import annotations

from ..db import ScenarioRepository
from ..models import Scenario
from ..validation import validate_scenario


class ScenarioController:
    def __init__(self, repo: ScenarioRepository) -> None:
        self.repo = repo

    def save(self, loan_id: int, name: str, extra_monthly: float) -> Scenario:
        validate_scenario(name, extra_monthly)
        return self.repo.create(
            Scenario(
                id=None,
                loan_id=loan_id,
                name=name.strip(),
                extra_monthly=extra_monthly,
            )
        )

    def list_for_loan(self, loan_id: int) -> list[Scenario]:
        return self.repo.list_for_loan(loan_id)

    def delete(self, scenario_id: int) -> bool:
        return self.repo.delete(scenario_id)

