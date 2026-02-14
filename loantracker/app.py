from __future__ import annotations

from nicegui import ui

from .config import DB_PATH
from .controllers import LoanController, PaymentController, ProjectionController, ScenarioController
from .db import Database, LoanRepository, PaymentRepository, ScenarioRepository
from .strategies import DailyPayoffStrategy
from .views import LoanTrackerView


def main() -> None:
    db = Database(DB_PATH)
    db.init()

    loan_repo = LoanRepository(db)
    payment_repo = PaymentRepository(db)
    scenario_repo = ScenarioRepository(db)

    loan_controller = LoanController(loan_repo)
    payment_controller = PaymentController(payment_repo)
    scenario_controller = ScenarioController(scenario_repo)
    projection_controller = ProjectionController(DailyPayoffStrategy(), payment_repo, loan_repo)

    view = LoanTrackerView(loan_controller, payment_controller, scenario_controller, projection_controller)

    @ui.page("/")
    def index() -> None:
        view.build()

    ui.run(title="Loan Tracker", reload=False)


if __name__ == "__main__":
    main()

