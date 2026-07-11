from __future__ import annotations

import pandas as pd


def build_order_service_detail(orders: pd.DataFrame, shipments: pd.DataFrame) -> pd.DataFrame:
    orders = orders.copy()
    shipments = shipments.copy()

    for column in ("order_date", "promised_date"):
        orders[column] = pd.to_datetime(orders[column])
    for column in ("ship_date", "delivery_date", "promised_date"):
        shipments[column] = pd.to_datetime(shipments[column])

    order_level = (
        orders.groupby(
            ["order_id", "customer_id", "warehouse", "order_date", "promised_date"],
            as_index=False,
        )
        .agg(
            units_ordered=("units_ordered", "sum"),
            units_shipped=("units_shipped", "sum"),
            revenue=("revenue", "sum"),
            line_count=("order_line_id", "nunique"),
        )
    )
    order_level["order_fill_rate"] = (
        order_level["units_shipped"] / order_level["units_ordered"].replace(0, pd.NA)
    ).fillna(0.0)
    order_level["in_full"] = order_level["units_shipped"] >= order_level["units_ordered"]

    shipment_cols = [
        "order_id", "shipment_id", "carrier", "delivery_date", "freight_cost",
        "handling_cost", "exception_cost", "shipment_weight_kg", "on_time",
    ]
    detail = order_level.merge(shipments[shipment_cols], on="order_id", how="left", validate="one_to_one")
    detail["on_time"] = detail["on_time"].astype("boolean").fillna(False).astype(bool)
    detail["otif"] = detail["on_time"] & detail["in_full"]
    detail["logistics_cost"] = (
        detail[["freight_cost", "handling_cost", "exception_cost"]].fillna(0).sum(axis=1)
    )
    weight = detail["shipment_weight_kg"].astype(float)
    freight = detail["freight_cost"].astype(float)
    detail["freight_cost_per_kg"] = freight.div(weight.where(weight.ne(0))).fillna(0.0).astype(float)
    detail["delivery_delay_days"] = (
        detail["delivery_date"] - detail["promised_date"]
    ).dt.days.fillna(0).astype(int)

    return detail.sort_values("order_id").reset_index(drop=True)


def build_daily_service_metrics(detail: pd.DataFrame) -> pd.DataFrame:
    daily = (
        detail.groupby("order_date", as_index=False)
        .agg(
            order_count=("order_id", "nunique"),
            units_ordered=("units_ordered", "sum"),
            units_shipped=("units_shipped", "sum"),
            revenue=("revenue", "sum"),
            on_time_rate=("on_time", "mean"),
            complete_order_rate=("in_full", "mean"),
            otif_rate=("otif", "mean"),
            logistics_cost=("logistics_cost", "sum"),
        )
        .sort_values("order_date")
    )
    daily["unit_fill_rate"] = daily["units_shipped"] / daily["units_ordered"]
    daily["rolling_30d_otif"] = daily["otif_rate"].rolling(30, min_periods=1).mean()
    daily["rolling_30d_revenue"] = daily["revenue"].rolling(30, min_periods=1).sum()
    return daily


def build_carrier_scorecard(detail: pd.DataFrame) -> pd.DataFrame:
    scorecard = (
        detail.groupby("carrier", as_index=False)
        .agg(
            order_count=("order_id", "nunique"),
            on_time_rate=("on_time", "mean"),
            otif_rate=("otif", "mean"),
            avg_delay_days=("delivery_delay_days", "mean"),
            freight_cost=("freight_cost", "sum"),
            shipment_weight_kg=("shipment_weight_kg", "sum"),
        )
    )
    scorecard["freight_cost_per_kg"] = scorecard["freight_cost"] / scorecard["shipment_weight_kg"]
    scorecard["otif_rank"] = scorecard["otif_rate"].rank(method="dense", ascending=False).astype(int)
    return scorecard.sort_values(["otif_rank", "carrier"]).reset_index(drop=True)
