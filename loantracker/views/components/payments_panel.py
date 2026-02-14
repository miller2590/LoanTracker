"""Payments panel component for recording and managing extra payments."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from ...controllers import PaymentController
from .currency_input import currency_input, parse_currency


class PaymentsPanel:
    """Panel for recording extra payments and viewing payment history."""

    def __init__(
        self,
        payment_controller: PaymentController,
        get_selected_loan_id: callable,
        on_payment_changed: callable = None,
    ) -> None:
        self.payment_controller = payment_controller
        self.get_selected_loan_id = get_selected_loan_id
        self.on_payment_changed = on_payment_changed
        self._payments_container: ui.column | None = None
        self._amount_input: ui.input | None = None
        self._date_input: ui.input | None = None
        self._note_input: ui.input | None = None

    def build(self) -> None:
        """Build the payments panel UI."""
        ui.label("Record Extra Payment").classes("text-subtitle1 font-medium")
        ui.separator()

        self._amount_input = currency_input("Payment Amount ($)").classes("w-full")

        with ui.input("Payment Date").classes("w-full") as self._date_input:
            self._date_input.value = date.today().isoformat()
            with ui.menu().props("no-parent-event") as menu:
                with ui.date(value=date.today().isoformat()).bind_value(self._date_input):
                    with ui.row().classes("justify-end"):
                        ui.button("Close", on_click=menu.close).props("flat")
            with self._date_input.add_slot("append"):
                ui.icon("edit_calendar").on("click", menu.open).classes("cursor-pointer")

        self._note_input = ui.input("Note (optional)").classes("w-full")

        ui.button(
            "Record Payment",
            icon="add",
            on_click=self._add_payment
        ).classes("w-full mt-2").props("color=primary")

        ui.separator().classes("my-4")
        ui.label("Payment History").classes("text-subtitle1 font-medium")
        self._payments_container = ui.column().classes("w-full max-h-48 overflow-auto")

    async def _add_payment(self) -> None:
        """Add a new payment."""
        loan_id = self.get_selected_loan_id()
        if not loan_id:
            ui.notify("Please select a loan first", type="warning")
            return
        try:
            payment_dt = date.fromisoformat(self._date_input.value) if self._date_input.value else date.today()
            amount_val = parse_currency(self._amount_input.value)
            self.payment_controller.create(
                loan_id,
                amount_val,
                payment_dt,
                self._note_input.value,
            )
            ui.notify("Payment recorded successfully!", type="positive")
            self._amount_input.value = None
            self._note_input.value = ""
            if self.on_payment_changed:
                self.on_payment_changed()
        except Exception as exc:
            ui.notify(str(exc), type="negative")

    def refresh(self, loan_id: int | None) -> None:
        """Refresh the payment history list."""
        if not self._payments_container:
            return
        self._payments_container.clear()

        if not loan_id:
            return

        payments = self.payment_controller.list_for_loan(loan_id)

        with self._payments_container:
            if not payments:
                ui.label("No extra payments recorded").classes("text-grey italic text-sm")
            else:
                for payment in reversed(payments[-10:]):  # Show last 10
                    with ui.row().classes("w-full items-center gap-2 py-1"):
                        ui.label(payment.payment_date.strftime("%b %d, %Y")).classes("text-caption flex-1")
                        ui.label(f"+${payment.amount:,.2f}").classes("text-positive font-medium")
                        ui.button(
                            icon="edit",
                            on_click=lambda p=payment: self._show_edit_dialog(p)
                        ).props("flat round dense size=sm").tooltip("Edit Payment")
                        ui.button(
                            icon="delete",
                            on_click=lambda p=payment: self._confirm_delete(p)
                        ).props("flat round dense size=sm color=negative").tooltip("Delete Payment")

    def _show_edit_dialog(self, payment) -> None:
        """Show dialog to edit a payment."""
        with ui.dialog() as dialog, ui.card().classes("w-80"):
            ui.label("Edit Payment").classes("text-h6 text-primary")
            ui.separator()

            amount_input = currency_input("Payment Amount ($)", payment.amount).classes("w-full")

            with ui.input("Payment Date").classes("w-full") as date_input:
                date_input.value = payment.payment_date.isoformat()
                with ui.menu().props("no-parent-event") as menu:
                    with ui.date(value=payment.payment_date.isoformat()).bind_value(date_input):
                        with ui.row().classes("justify-end"):
                            ui.button("Close", on_click=menu.close).props("flat")
                with date_input.add_slot("append"):
                    ui.icon("edit_calendar").on("click", menu.open).classes("cursor-pointer")

            note_input = ui.input("Note (optional)", value=payment.note or "").classes("w-full")

            async def save_payment() -> None:
                try:
                    payment_dt = date.fromisoformat(date_input.value) if date_input.value else payment.payment_date
                    amount_val = parse_currency(amount_input.value)
                    updated = self.payment_controller.update(
                        payment.id,
                        amount_val,
                        payment_dt,
                        note_input.value,
                    )
                    if updated:
                        ui.notify("Payment updated!", type="positive")
                        dialog.close()
                        if self.on_payment_changed:
                            self.on_payment_changed()
                    else:
                        ui.notify("Failed to update payment", type="negative")
                except Exception as exc:
                    ui.notify(str(exc), type="negative")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Save", icon="save", on_click=save_payment).props("color=primary")

        dialog.open()

    def _confirm_delete(self, payment) -> None:
        """Show confirmation dialog to delete a payment."""
        with ui.dialog() as dialog, ui.card().classes("w-80"):
            ui.label("Delete Payment?").classes("text-h6 text-negative")
            ui.separator()
            ui.label(f"Delete payment of ${payment.amount:,.2f}?").classes("my-2")
            ui.label(f"Date: {payment.payment_date.strftime('%b %d, %Y')}").classes("text-caption text-grey")

            async def do_delete() -> None:
                if self.payment_controller.delete(payment.id):
                    ui.notify("Payment deleted", type="positive")
                    dialog.close()
                    if self.on_payment_changed:
                        self.on_payment_changed()
                else:
                    ui.notify("Failed to delete payment", type="negative")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Delete", icon="delete", on_click=do_delete).props("color=negative")

        dialog.open()

