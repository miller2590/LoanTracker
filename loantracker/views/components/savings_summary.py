"""Savings summary card component."""

from __future__ import annotations

from datetime import date, timedelta

from nicegui import ui

from ...controllers import LoanController, ProjectionController
from ...models import Loan
from .currency_input import parse_currency


class SavingsSummaryCard:
    """Displays savings comparison between baseline and what-if scenarios."""

    def __init__(
        self,
        loan_controller: LoanController,
        projection_controller: ProjectionController,
    ) -> None:
        self.loan_controller = loan_controller
        self.projection_controller = projection_controller
        self._container: ui.column | None = None

    def build(self) -> ui.column:
        """Build and return the savings summary container."""
        self._container = ui.column().classes("w-full")
        return self._container

    def refresh(self, loan_id: int | None, extra_monthly: float) -> None:
        """Refresh the savings summary display."""
        if not self._container:
            return
        self._container.clear()

        if not loan_id:
            with self._container:
                ui.label("No loan selected").classes("text-grey italic")
            return

        loan = self.loan_controller.get(loan_id)
        if not loan:
            return

        try:
            # Get projections
            baseline = self.projection_controller.project(loan_id, 0.0, "monthly")
            whatif = self.projection_controller.project(loan_id, extra_monthly, "monthly")

            # Calculate totals
            baseline_total_paid = len(baseline) * loan.minimum_payment
            baseline_interest = baseline_total_paid - loan.principal

            whatif_payments = len(whatif)
            whatif_total_paid = whatif_payments * (loan.minimum_payment + extra_monthly)
            whatif_interest = whatif_total_paid - loan.principal

            # Calculate savings
            months_saved = len(baseline) - len(whatif)
            interest_saved = baseline_interest - whatif_interest

            # Get payoff dates
            baseline_payoff = baseline[-1].point_date if baseline else None
            whatif_payoff = whatif[-1].point_date if whatif else None

            # Calculate crossover dates
            baseline_crossover = self._find_principal_crossover(loan, 0.0)
            whatif_crossover = self._find_principal_crossover(loan, extra_monthly) if extra_monthly > 0 else None

            with self._container:
                if extra_monthly > 0 and months_saved > 0:
                    self._build_comparison_view(
                        months_saved, interest_saved,
                        baseline_payoff, whatif_payoff,
                        baseline_interest, whatif_interest,
                        baseline_crossover, whatif_crossover,
                    )
                else:
                    self._build_baseline_view(
                        baseline, baseline_payoff,
                        baseline_interest, baseline_total_paid,
                        baseline_crossover,
                    )

        except Exception as exc:
            with self._container:
                ui.label(f"Error calculating savings: {exc}").classes("text-negative")

    def _build_comparison_view(
        self,
        months_saved: int,
        interest_saved: float,
        baseline_payoff: date | None,
        whatif_payoff: date | None,
        baseline_interest: float,
        whatif_interest: float,
        baseline_crossover: date | None,
        whatif_crossover: date | None,
    ) -> None:
        """Build the comparison view showing baseline vs what-if."""
        # Savings highlight box
        with ui.card().classes("w-full bg-green-50 mb-4").props("flat bordered"):
            with ui.row().classes("w-full justify-center gap-12 p-2"):
                with ui.column().classes("gap-0 items-center"):
                    ui.label("Time Saved").classes("text-caption text-positive font-medium")
                    years = months_saved // 12
                    months = months_saved % 12
                    time_str = ""
                    if years > 0:
                        time_str += f"{years} yr "
                    if months > 0:
                        time_str += f"{months} mo"
                    ui.label(time_str.strip() or "0 mo").classes("text-h5 text-positive font-bold")
                with ui.column().classes("gap-0 items-center"):
                    ui.label("Interest Saved").classes("text-caption text-positive font-medium")
                    ui.label(f"${interest_saved:,.2f}").classes("text-h5 text-positive font-bold")

        # Side-by-side comparison
        with ui.row().classes("w-full gap-4"):
            # Baseline column
            with ui.card().classes("flex-1").props("flat bordered"):
                ui.label("Baseline").classes("text-h6 text-primary font-bold mb-2")
                ui.separator()
                with ui.column().classes("gap-3 mt-2"):
                    self._stat_row("Payoff Date",
                        baseline_payoff.strftime("%b %Y") if baseline_payoff else "N/A",
                        "text-primary")
                    self._stat_row("Total Interest", f"${baseline_interest:,.2f}", "text-primary")
                    self._stat_row("Principal > Interest",
                        baseline_crossover.strftime("%b %Y") if baseline_crossover else "N/A",
                        "text-primary")

            # What-if column
            with ui.card().classes("flex-1 bg-green-50").props("flat bordered"):
                ui.label("What-If").classes("text-h6 text-positive font-bold mb-2")
                ui.separator()
                with ui.column().classes("gap-3 mt-2"):
                    self._stat_row("Payoff Date",
                        whatif_payoff.strftime("%b %Y") if whatif_payoff else "N/A",
                        "text-positive")
                    self._stat_row("Total Interest", f"${whatif_interest:,.2f}", "text-positive")
                    self._stat_row("Principal > Interest",
                        whatif_crossover.strftime("%b %Y") if whatif_crossover else "N/A",
                        "text-positive")

    def _build_baseline_view(
        self,
        baseline: list,
        baseline_payoff: date | None,
        baseline_interest: float,
        baseline_total_paid: float,
        baseline_crossover: date | None,
    ) -> None:
        """Build the baseline-only view when no extra payment is set."""
        with ui.row().classes("w-full gap-8"):
            with ui.column().classes("gap-1"):
                ui.label("Payoff Date").classes("text-caption text-grey")
                ui.label(baseline_payoff.strftime("%b %Y") if baseline_payoff else "N/A").classes("text-h6")
            with ui.column().classes("gap-1"):
                ui.label("Payments Remaining").classes("text-caption text-grey")
                ui.label(f"{len(baseline)} payments").classes("text-h6")
            with ui.column().classes("gap-1"):
                ui.label("Total Interest").classes("text-caption text-grey")
                ui.label(f"${baseline_interest:,.2f}").classes("text-h6")
            with ui.column().classes("gap-1"):
                ui.label("Total Cost").classes("text-caption text-grey")
                ui.label(f"${baseline_total_paid:,.2f}").classes("text-h6")
            with ui.column().classes("gap-1"):
                ui.label("Principal > Interest").classes("text-caption text-grey")
                ui.label(baseline_crossover.strftime("%b %Y") if baseline_crossover else "N/A").classes("text-h6")
        ui.label("Add extra monthly payment in What-If tab to see potential savings").classes(
            "text-caption text-grey mt-2 italic"
        )

    @staticmethod
    def _stat_row(label: str, value: str, value_class: str) -> None:
        """Create a label-value row."""
        with ui.row().classes("justify-between w-full"):
            ui.label(label).classes("text-body2 text-grey-7")
            ui.label(value).classes(f"text-body1 font-medium {value_class}")

    @staticmethod
    def _find_principal_crossover(loan: Loan, extra_monthly: float) -> date | None:
        """Find when principal portion of payment exceeds interest portion."""
        balance = loan.principal
        if balance <= 0:
            return None

        daily_rate = (loan.apr / 100.0) / 365.0
        monthly_payment = loan.minimum_payment + extra_monthly
        current_date = date.today()
        last_month = (current_date.year, current_date.month)

        max_days = 365 * 100

        for _ in range(max_days):
            current_date += timedelta(days=1)
            daily_interest = balance * daily_rate
            balance += daily_interest

            current_month = (current_date.year, current_date.month)
            if current_month != last_month:
                monthly_interest = balance * (loan.apr / 100.0) / 12.0
                payment = min(monthly_payment, balance)
                interest_portion = min(monthly_interest, payment)
                principal_portion = payment - interest_portion

                if principal_portion > interest_portion:
                    return current_date

                balance -= payment
                last_month = current_month

            if balance <= 0:
                break

        return None

