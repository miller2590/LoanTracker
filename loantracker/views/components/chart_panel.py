"""Chart panel component for loan payoff projections."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from ...controllers import ProjectionController


class ChartPanel:
    """Panel displaying the loan payoff projection chart."""

    def __init__(self, projection_controller: ProjectionController) -> None:
        self.projection_controller = projection_controller
        self._chart: ui.echart | None = None
        self._granularity_select: ui.select | None = None
        self._on_granularity_change: Callable[[], None] | None = None

    @property
    def granularity(self) -> str:
        """Get the current granularity setting."""
        return self._granularity_select.value if self._granularity_select else "monthly"

    def build(self, on_granularity_change: Callable[[], None]) -> ui.echart:
        """Build and return the chart panel."""
        self._on_granularity_change = on_granularity_change

        with ui.row().classes("w-full items-center mb-2"):
            ui.label("Payoff Projection").classes("text-h6 text-primary")
            ui.space()
            self._granularity_select = ui.select(
                options={"monthly": "Monthly", "yearly": "Yearly"},
                value="monthly",
                on_change=lambda: on_granularity_change(),
            ).props("dense outlined").classes("w-32")

        self._chart = ui.echart(self._empty_chart()).classes("w-full h-96")
        return self._chart

    def update(
        self,
        loan_id: int | None,
        extra_monthly: float,
        granularity: str,
    ) -> tuple[str, str]:
        """Update the chart with new projection data.

        Returns:
            Tuple of (baseline_payoff_str, whatif_payoff_str) for use by other components.
        """
        if not self._chart:
            return "N/A", "N/A"

        if not loan_id:
            self._set_options(self._empty_chart())
            return "N/A", "N/A"

        try:
            baseline = self.projection_controller.project(loan_id, 0.0, granularity)
            whatif = self.projection_controller.project(loan_id, extra_monthly, granularity)
            labels, baseline_values, whatif_values = self._align_series(baseline, whatif, granularity)

            # Get actual payoff dates
            baseline_payoff = "N/A"
            for point in baseline:
                if point.balance == 0:
                    baseline_payoff = point.point_date.strftime("%b %Y")
                    break

            whatif_payoff = "N/A"
            for point in whatif:
                if point.balance == 0:
                    whatif_payoff = point.point_date.strftime("%b %Y")
                    break

            display_labels = self._format_labels(labels, granularity)

            # Build chart series
            series = [
                {
                    "name": f"Baseline (Payoff: {baseline_payoff})",
                    "type": "line",
                    "data": baseline_values,
                    "smooth": False,
                    "connectNulls": True,
                    "itemStyle": {"color": "#3b82f6"},
                    "areaStyle": {"opacity": 0.1},
                },
            ]

            legend_data = [f"Baseline (Payoff: {baseline_payoff})"]

            if extra_monthly > 0:
                series.append({
                    "name": f"+${extra_monthly:,.2f}/mo Extra Principal (Payoff: {whatif_payoff})",
                    "type": "line",
                    "data": whatif_values,
                    "smooth": False,
                    "connectNulls": True,
                    "itemStyle": {"color": "#10b981"},
                    "areaStyle": {"opacity": 0.1},
                })
                legend_data.append(f"+${extra_monthly:,.2f}/mo Extra Principal (Payoff: {whatif_payoff})")

            self._set_options({
                "tooltip": {"trigger": "axis"},
                "legend": {
                    "data": legend_data,
                    "bottom": 0,
                    "textStyle": {"fontSize": 11},
                },
                "grid": {"bottom": 80, "left": 70, "right": 20},
                "xAxis": {
                    "type": "category",
                    "data": display_labels,
                    "axisLabel": {"rotate": 45, "fontSize": 10, "interval": "auto"},
                },
                "yAxis": {
                    "type": "value",
                    "name": "Balance",
                    "nameTextStyle": {"fontSize": 11},
                    "axisLabel": {"fontSize": 10},
                },
                "series": series,
            })

            return baseline_payoff, whatif_payoff

        except Exception as exc:
            ui.notify(str(exc), type="negative")
            return "N/A", "N/A"

    def _set_options(self, options: dict) -> None:
        """Set chart options and update."""
        if not self._chart:
            return
        self._chart.options.clear()
        self._chart.options.update(options)
        self._chart.update()

    @staticmethod
    def _empty_chart() -> dict:
        """Return empty chart configuration."""
        return {
            "title": {
                "text": "Select a loan to view projections",
                "left": "center",
                "top": "center",
                "textStyle": {"color": "#999"},
            },
            "xAxis": {"type": "category", "data": []},
            "yAxis": {"type": "value"},
            "series": [],
        }

    @staticmethod
    def _align_series(baseline: list, whatif: list, granularity: str) -> tuple[list[str], list[float], list[float]]:
        """Align two series to shared x-axis labels."""
        baseline_map = {point.point_date.isoformat(): point.balance for point in baseline}
        whatif_map = {point.point_date.isoformat(): point.balance for point in whatif}

        # Find payoff dates
        baseline_payoff = None
        whatif_payoff = None
        for point in baseline:
            if point.balance == 0:
                baseline_payoff = point.point_date.isoformat()
                break
        for point in whatif:
            if point.balance == 0:
                whatif_payoff = point.point_date.isoformat()
                break

        all_dates = sorted(set(baseline_map.keys()) | set(whatif_map.keys()))

        if granularity == "yearly":
            regular_dates = [d for d in all_dates if d.endswith('-12-31')]
            final_year = None
            if baseline_payoff:
                final_year = baseline_payoff[:4]
            if whatif_payoff:
                wy = whatif_payoff[:4]
                if final_year is None or wy > final_year:
                    final_year = wy
            if final_year:
                final_dec = f"{final_year}-12-31"
                if final_dec not in regular_dates:
                    regular_dates.append(final_dec)
                    regular_dates.sort()
        else:
            regular_dates = all_dates

        labels = regular_dates
        baseline_values: list[float] = []
        whatif_values: list[float] = []

        for label in labels:
            if baseline_payoff and label >= baseline_payoff:
                baseline_values.append(0.0)
            elif label in baseline_map:
                baseline_values.append(baseline_map[label])
            else:
                baseline_values.append(baseline_values[-1] if baseline_values else 0.0)

            if whatif_payoff and label >= whatif_payoff:
                whatif_values.append(0.0)
            elif label in whatif_map:
                whatif_values.append(whatif_map[label])
            else:
                whatif_values.append(whatif_values[-1] if whatif_values else 0.0)

        return labels, baseline_values, whatif_values

    @staticmethod
    def _format_labels(labels: list[str], granularity: str) -> list[str]:
        """Format ISO date labels to shorter display format."""
        if granularity == "yearly":
            return [label[:4] for label in labels]
        else:
            return [label[:7] for label in labels]

