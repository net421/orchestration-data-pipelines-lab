from __future__ import annotations

import pandas as pd

from .errors import DataContractError

ORDER_COLUMNS = {
    "order_line_id", "order_id", "customer_id", "warehouse", "order_date",
    "promised_date", "sku", "supplier_id", "units_ordered", "units_shipped",
    "unit_price", "unit_weight_kg", "revenue",
}
SHIPMENT_COLUMNS = {
    "shipment_id", "order_id", "carrier", "warehouse", "ship_date",
    "delivery_date", "promised_date", "shipment_weight_kg", "freight_cost",
    "handling_cost", "exception_cost", "on_time",
}


def _require_columns(df: pd.DataFrame, required: set[str], source: str) -> None:
    missing = sorted(required.difference(df.columns))
    if missing:
        raise DataContractError(f"{source} is missing required columns: {missing}")


def validate_sources(sources: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    orders = sources["orders"]
    shipments = sources["shipments"]
    _require_columns(orders, ORDER_COLUMNS, "orders")
    _require_columns(shipments, SHIPMENT_COLUMNS, "shipments")

    checks: list[dict[str, object]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})
        if not passed:
            raise DataContractError(f"{name}: {detail}")

    add(
        "order_line_id_unique",
        not orders["order_line_id"].duplicated().any(),
        "ERP order-line key must be unique.",
    )
    add(
        "shipment_order_unique",
        not shipments["order_id"].duplicated().any(),
        "The sample contract expects one shipment record per order.",
    )
    numeric_order_cols = ["units_ordered", "units_shipped", "unit_price", "unit_weight_kg", "revenue"]
    add(
        "order_values_non_negative",
        bool((orders[numeric_order_cols] >= 0).all().all()),
        "Order quantities, price, weight, and revenue must be non-negative.",
    )
    add(
        "shipped_not_above_ordered",
        bool((orders["units_shipped"] <= orders["units_ordered"]).all()),
        "Shipped units cannot exceed ordered units in this simulation.",
    )
    shipment_orders = set(shipments["order_id"])
    source_orders = set(orders["order_id"])
    add(
        "shipment_orders_exist",
        shipment_orders.issubset(source_orders),
        "Every shipment must reference an ERP order.",
    )
    add(
        "dates_parseable",
        bool(pd.to_datetime(orders["order_date"], errors="coerce").notna().all())
        and bool(pd.to_datetime(shipments["delivery_date"], errors="coerce").notna().all()),
        "Required order and delivery dates must be parseable.",
    )
    return checks


def validate_outputs(
    order_detail: pd.DataFrame,
    daily_metrics: pd.DataFrame,
    carrier_scorecard: pd.DataFrame,
) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})
        if not passed:
            raise DataContractError(f"{name}: {detail}")

    add("one_row_per_order", not order_detail["order_id"].duplicated().any(), "Output grain is order.")
    add(
        "fill_rate_range",
        bool(order_detail["order_fill_rate"].between(0, 1).all()),
        "Order fill rate must remain between 0 and 1.",
    )
    add(
        "otif_requires_components",
        bool((~order_detail["otif"] | (order_detail["on_time"] & order_detail["in_full"])).all()),
        "OTIF can only be true when both on-time and in-full are true.",
    )
    add(
        "daily_metrics_non_empty",
        not daily_metrics.empty,
        "Daily service mart must contain rows.",
    )
    add(
        "carrier_scorecard_non_empty",
        not carrier_scorecard.empty,
        "Carrier scorecard must contain rows.",
    )
    return checks
