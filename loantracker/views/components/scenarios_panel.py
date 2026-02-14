"""Scenarios panel component for what-if analysis."""

from __future__ import annotations

from nicegui import ui

from ...controllers import ScenarioController
from ...models import Scenario
from .currency_input import currency_input, parse_currency


class ScenariosPanel:
    """Panel for creating and managing what-if payment scenarios."""

    def __init__(
        self,
        scenario_controller: ScenarioController,
        get_selected_loan_id: callable,
        on_scenario_changed: callable = None,
    ) -> None:
        self.scenario_controller = scenario_controller
        self.get_selected_loan_id = get_selected_loan_id
        self.on_scenario_changed = on_scenario_changed
        self._extra_monthly_input: ui.input | None = None
        self._scenario_select: ui.select | None = None

    @property
    def extra_monthly_input(self) -> ui.input | None:
        """Get the extra monthly payment input element."""
        return self._extra_monthly_input

    def build(self, on_update_projection: callable) -> None:
        """Build the scenarios panel UI."""
        ui.label("Compare Payment Scenarios").classes("text-subtitle1 font-medium")
        ui.separator()

        self._extra_monthly_input = currency_input("Extra Principal Payment ($/mo)").classes("w-full")

        ui.button(
            "Update Projection",
            icon="refresh",
            on_click=on_update_projection
        ).classes("w-full mt-2").props("color=primary")

        ui.separator().classes("my-4")
        ui.label("Save Scenario").classes("text-subtitle1 font-medium")

        scenario_name = ui.input("Scenario Name").classes("w-full")

        async def save_scenario() -> None:
            loan_id = self.get_selected_loan_id()
            if not loan_id:
                ui.notify("Please select a loan first", type="warning")
                return
            try:
                extra_val = parse_currency(self._extra_monthly_input.value) if self._extra_monthly_input else 0
                scenario = self.scenario_controller.save(
                    loan_id,
                    scenario_name.value or "",
                    extra_val,
                )
                ui.notify(f"Scenario '{scenario.name}' saved!", type="positive")
                scenario_name.value = ""
                self.refresh(loan_id, selected=scenario)
                if self.on_scenario_changed:
                    self.on_scenario_changed()
            except Exception as exc:
                ui.notify(str(exc), type="negative")

        ui.button("Save Scenario", icon="save", on_click=save_scenario).classes("w-full").props("outline")

        ui.separator().classes("my-4")
        ui.label("Load Saved Scenario").classes("text-subtitle1 font-medium")
        self._scenario_select = ui.select(
            label="Saved Scenarios",
            options={},
            on_change=self._on_scenario_selected
        ).classes("w-full")

    def refresh(self, loan_id: int | None, selected: Scenario | None = None) -> None:
        """Refresh the saved scenarios list."""
        if not self._scenario_select:
            return
        options = {}
        if loan_id:
            scenarios = self.scenario_controller.list_for_loan(loan_id)
            options = {sc.id: f"{sc.name} (+${sc.extra_monthly:,.0f}/mo)" for sc in scenarios if sc.id}
        self._scenario_select.set_options(options)
        if selected and selected.id in options:
            self._scenario_select.value = selected.id

    def _on_scenario_selected(self) -> None:
        """Handle scenario selection change."""
        if not self._scenario_select or not self._extra_monthly_input:
            return
        loan_id = self.get_selected_loan_id()
        if not loan_id or not self._scenario_select.value:
            return
        scenarios = self.scenario_controller.list_for_loan(loan_id)
        selected = next((sc for sc in scenarios if sc.id == self._scenario_select.value), None)
        if selected:
            self._extra_monthly_input.value = f"{selected.extra_monthly:,.2f}"
            if self.on_scenario_changed:
                self.on_scenario_changed()

    def get_extra_monthly(self) -> float:
        """Get the current extra monthly payment value."""
        if not self._extra_monthly_input:
            return 0.0
        return parse_currency(self._extra_monthly_input.value)

