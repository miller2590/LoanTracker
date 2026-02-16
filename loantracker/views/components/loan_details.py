"""Loan details card component."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from ...controllers import LoanController, PaymentController, ProjectionController
from ...models import Loan


class LoanDetailsCard:
    """Displays loan details with edit capability."""

    def __init__(
        self,
        loan_controller: LoanController,
        payment_controller: PaymentController,
        projection_controller: ProjectionController,
        on_loan_updated: Callable[[Loan], None] | None = None,
    ) -> None:
        self.loan_controller = loan_controller
        self.payment_controller = payment_controller
        self.projection_controller = projection_controller
        self.on_loan_updated = on_loan_updated
        self._container: ui.column | None = None

    def build(self) -> ui.column:
        """Build and return the loan details container."""
        self._container = ui.column().classes("w-full")
        return self._container

    def refresh(self, loan_id: int | None) -> None:
        """Refresh the loan details display."""
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

        payments = self.payment_controller.list_for_loan(loan_id)
        total_extra_paid = sum(p.amount for p in payments)
        current_balance = self.projection_controller.current_balance(loan_id)

        with self._container:
            with ui.row().classes("w-full items-center"):
                with ui.row().classes("flex-1 gap-8"):
                    with ui.column().classes("gap-1"):
                        ui.label("Original Principal").classes("text-caption text-grey")
                        ui.label(f"${loan.principal:,.2f}").classes("text-h6")
                    with ui.column().classes("gap-1"):
                        ui.label("Current Balance").classes("text-caption text-grey")
                        ui.label(f"${current_balance:,.2f}").classes("text-h6 text-primary")
                    with ui.column().classes("gap-1"):
                        ui.label("Interest Rate").classes("text-caption text-grey")
                        ui.label(f"{loan.apr:.3f}%").classes("text-h6")
                    with ui.column().classes("gap-1"):
                        ui.label("Min Payment").classes("text-caption text-grey")
                        ui.label(f"${loan.minimum_payment:,.2f}/mo").classes("text-h6")
                    with ui.column().classes("gap-1"):
                        ui.label("Extra Principal Paid").classes("text-caption text-grey")
                        ui.label(f"${total_extra_paid:,.2f}").classes("text-h6 text-positive")
                ui.button(
                    icon="edit",
                    on_click=lambda: self._show_edit_dialog(loan)
                ).props("flat round dense").tooltip("Edit Loan")

    def _show_edit_dialog(self, loan: Loan) -> None:
        """Show dialog to edit loan details."""
        from datetime import date
        from .currency_input import currency_input, parse_currency

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Edit Loan").classes("text-h6 text-primary")
            ui.separator()

            name_input = ui.input("Loan Name", value=loan.name).classes("w-full")
            principal_input = currency_input("Principal Amount ($)", loan.principal).classes("w-full")
            apr_input = ui.number(
                "Annual Interest Rate (%)",
                format="%.3f",
                value=loan.apr,
                validation={"Must be 0-100": lambda v: v is None or 0 < v < 100}
            ).classes("w-full")
            min_payment_input = currency_input("Minimum Monthly Payment ($)", loan.minimum_payment).classes("w-full")

            with ui.input("Start Date").classes("w-full") as start_date_input:
                start_date_input.value = loan.start_date.isoformat()
                with ui.menu().props("no-parent-event") as menu:
                    with ui.date(value=loan.start_date.isoformat()).bind_value(start_date_input):
                        with ui.row().classes("justify-end"):
                            ui.button("Close", on_click=menu.close).props("flat")
                with start_date_input.add_slot("append"):
                    ui.icon("edit_calendar").on("click", menu.open).classes("cursor-pointer")

            async def save_loan() -> None:
                try:
                    start_dt = date.fromisoformat(start_date_input.value) if start_date_input.value else loan.start_date
                    principal_val = parse_currency(principal_input.value)
                    min_payment_val = parse_currency(min_payment_input.value)
                    updated = self.loan_controller.update(
                        loan.id,
                        name_input.value or "",
                        principal_val,
                        float(apr_input.value or 0),
                        min_payment_val,
                        start_dt,
                    )
                    if updated:
                        ui.notify(f"Loan '{updated.name}' updated!", type="positive")
                        dialog.close()
                        if self.on_loan_updated:
                            self.on_loan_updated(updated)
                    else:
                        ui.notify("Failed to update loan", type="negative")
                except Exception as exc:
                    ui.notify(str(exc), type="negative")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Save Changes", icon="save", on_click=save_loan).props("color=primary")

        dialog.open()

