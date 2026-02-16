"""Main view for the LoanTracker application."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from ..controllers import LoanController, PaymentController, ProjectionController, ScenarioController
from ..models import Loan
from .components import (
    currency_input,
    parse_currency,
    LoanDetailsCard,
    PaymentsPanel,
    SavingsSummaryCard,
    ScenariosPanel,
    ChartPanel,
)


class LoanTrackerView:
    """Main application view orchestrating all UI components."""

    def __init__(
        self,
        loan_controller: LoanController,
        payment_controller: PaymentController,
        scenario_controller: ScenarioController,
        projection_controller: ProjectionController,
    ) -> None:
        self.loan_controller = loan_controller
        self.payment_controller = payment_controller
        self.scenario_controller = scenario_controller
        self.projection_controller = projection_controller

        # UI element references
        self._loan_select: ui.select | None = None

        # Component instances
        self._loan_details: LoanDetailsCard | None = None
        self._payments_panel: PaymentsPanel | None = None
        self._scenarios_panel: ScenariosPanel | None = None
        self._chart_panel: ChartPanel | None = None
        self._savings_card: SavingsSummaryCard | None = None

    def build(self) -> None:
        """Build the main application UI."""
        ui.colors(primary="#3b82f6")

        self._build_header()
        self._build_main_content()
        self._refresh_loans()

    def _build_header(self) -> None:
        """Build the application header."""
        with ui.header().classes("bg-primary text-white shadow-md"):
            ui.label("💰 Loan Payoff Tracker").classes("text-h5 font-bold")
            ui.space()
            with ui.row().classes("items-center gap-2"):
                self._loan_select = ui.select(
                    label="Active Loan",
                    options={},
                    on_change=self._on_loan_selected
                ).classes("min-w-64 bg-white/10").props("dark dense outlined")
                ui.button(
                    icon="add",
                    on_click=self._show_add_loan_dialog
                ).props("round dense").tooltip("Add New Loan")
                ui.button(
                    icon="delete",
                    on_click=self._confirm_delete_loan
                ).props("round dense color=negative").tooltip("Delete Loan")

    def _build_main_content(self) -> None:
        """Build the main content area."""
        with ui.row().classes("w-full flex-1 p-4 gap-4"):
            self._build_left_panel()
            self._build_right_panel()

    def _build_left_panel(self) -> None:
        """Build the left control panel."""
        with ui.card().classes("w-80 shrink-0"):
            with ui.tabs().classes("w-full") as tabs:
                payments_tab = ui.tab("Payments", icon="payment")
                scenarios_tab = ui.tab("What-If", icon="analytics")

            with ui.tab_panels(tabs, value=payments_tab).classes("w-full"):
                with ui.tab_panel(payments_tab):
                    self._payments_panel = PaymentsPanel(
                        self.payment_controller,
                        self._selected_loan_id,
                        on_payment_changed=self._on_payment_changed,
                    )
                    self._payments_panel.build()

                with ui.tab_panel(scenarios_tab):
                    self._scenarios_panel = ScenariosPanel(
                        self.scenario_controller,
                        self._selected_loan_id,
                        on_scenario_changed=self._refresh_chart,
                    )
                    self._scenarios_panel.build(on_update_projection=self._refresh_chart)

    def _build_right_panel(self) -> None:
        """Build the right content panel."""
        with ui.column().classes("flex-1 min-w-0 gap-4"):
            # Loan details card
            with ui.card().classes("w-full"):
                ui.label("Loan Details").classes("text-h6 text-primary")
                self._loan_details = LoanDetailsCard(
                    self.loan_controller,
                    self.payment_controller,
                    self.projection_controller,
                    on_loan_updated=self._on_loan_updated,
                )
                self._loan_details.build()

            # Chart card
            with ui.card().classes("w-full flex-1"):
                self._chart_panel = ChartPanel(self.projection_controller)
                self._chart_panel.build(on_granularity_change=self._refresh_chart)

            # Savings summary card
            with ui.card().classes("w-full"):
                ui.label("Savings Summary").classes("text-h6 text-primary")
                self._savings_card = SavingsSummaryCard(
                    self.loan_controller,
                    self.projection_controller,
                )
                self._savings_card.build()

    # === Loan Management ===

    def _show_add_loan_dialog(self) -> None:
        """Show dialog to add a new loan."""
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Add New Loan").classes("text-h6 text-primary")
            ui.separator()

            name_input = ui.input("Loan Name", placeholder="e.g., Car Loan, Mortgage").classes("w-full")
            principal_input = currency_input("Principal Amount ($)").classes("w-full")
            apr_input = ui.number(
                "Annual Interest Rate (%)",
                format="%.3f",
                validation={"Must be 0-100": lambda v: v is None or 0 < v < 100}
            ).classes("w-full")
            min_payment_input = currency_input("Minimum Monthly Payment ($)").classes("w-full")

            with ui.input("Start Date").classes("w-full") as start_date_input:
                start_date_input.value = date.today().isoformat()
                with ui.menu().props("no-parent-event") as menu:
                    with ui.date(value=date.today().isoformat()).bind_value(start_date_input):
                        with ui.row().classes("justify-end"):
                            ui.button("Close", on_click=menu.close).props("flat")
                with start_date_input.add_slot("append"):
                    ui.icon("edit_calendar").on("click", menu.open).classes("cursor-pointer")

            async def create_loan() -> None:
                try:
                    start_dt = date.fromisoformat(start_date_input.value) if start_date_input.value else date.today()
                    principal_val = parse_currency(principal_input.value)
                    min_payment_val = parse_currency(min_payment_input.value)
                    loan = self.loan_controller.create(
                        name_input.value or "",
                        principal_val,
                        float(apr_input.value or 0),
                        min_payment_val,
                        start_dt,
                    )
                    ui.notify(f"Loan '{loan.name}' created!", type="positive")
                    dialog.close()
                    self._refresh_loans(selected=loan)
                except Exception as exc:
                    ui.notify(str(exc), type="negative")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Create Loan", icon="add", on_click=create_loan).props("color=primary")

        dialog.open()

    def _confirm_delete_loan(self) -> None:
        """Show confirmation dialog to delete a loan."""
        loan_id = self._selected_loan_id()
        if not loan_id:
            ui.notify("No loan selected", type="warning")
            return

        loan = self.loan_controller.get(loan_id)
        if not loan:
            ui.notify("Loan not found", type="negative")
            return

        with ui.dialog() as dialog, ui.card().classes("w-80"):
            ui.label("Delete Loan?").classes("text-h6 text-negative")
            ui.separator()
            ui.label(f"Are you sure you want to delete '{loan.name}'?").classes("my-2")
            ui.label("This will also delete all payments and scenarios for this loan.").classes(
                "text-caption text-grey"
            )

            async def do_delete() -> None:
                if self.loan_controller.delete(loan_id):
                    ui.notify(f"Loan '{loan.name}' deleted", type="positive")
                    dialog.close()
                    self._refresh_loans()
                else:
                    ui.notify("Failed to delete loan", type="negative")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Delete", icon="delete", on_click=do_delete).props("color=negative")

        dialog.open()

    # === Refresh Methods ===

    def _refresh_loans(self, selected: Loan | None = None) -> None:
        """Refresh the loan selector and all dependent components."""
        if not self._loan_select:
            return

        loans = self.loan_controller.list_all()
        options = {loan.id: loan.name for loan in loans if loan.id}
        self._loan_select.set_options(options)

        if selected and selected.id in options:
            self._loan_select.value = selected.id
        elif loans:
            self._loan_select.value = loans[0].id
        else:
            self._loan_select.value = None

        self._refresh_all_components()

    def _refresh_all_components(self) -> None:
        """Refresh all UI components."""
        loan_id = self._selected_loan_id()

        if self._loan_details:
            self._loan_details.refresh(loan_id)
        if self._payments_panel:
            self._payments_panel.refresh(loan_id)
        if self._scenarios_panel:
            self._scenarios_panel.refresh(loan_id)
        self._refresh_chart()

    def _refresh_chart(self) -> None:
        """Refresh the chart and savings summary."""
        loan_id = self._selected_loan_id()
        extra_monthly = self._scenarios_panel.get_extra_monthly() if self._scenarios_panel else 0.0
        granularity = self._chart_panel.granularity if self._chart_panel else "monthly"

        if self._chart_panel:
            self._chart_panel.update(loan_id, extra_monthly, granularity)

        if self._savings_card:
            self._savings_card.refresh(loan_id, extra_monthly)

    # === Event Handlers ===

    def _on_loan_selected(self) -> None:
        """Handle loan selection change."""
        self._refresh_all_components()

    def _on_loan_updated(self, loan: Loan) -> None:
        """Handle loan update."""
        self._refresh_loans(selected=loan)

    def _on_payment_changed(self) -> None:
        """Handle payment add/edit/delete."""
        loan_id = self._selected_loan_id()
        if self._loan_details:
            self._loan_details.refresh(loan_id)
        if self._payments_panel:
            self._payments_panel.refresh(loan_id)
        self._refresh_chart()

    # === Helpers ===

    def _selected_loan_id(self) -> int | None:
        """Get the currently selected loan ID."""
        if not self._loan_select:
            return None
        return int(self._loan_select.value) if self._loan_select.value else None

