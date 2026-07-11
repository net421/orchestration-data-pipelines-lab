"""Generate compact deterministic ERP/WMS/TMS-style source files."""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path


RNG = random.Random(421)
WAREHOUSES = ["WH-NORTH", "WH-SOUTH", "WH-CENTRAL"]
REGIONS = ["North", "South", "Central", "West"]
SEGMENTS = ["Enterprise", "Mid-Market", "SMB"]
CARRIERS = ["CarrierA", "CarrierB", "CarrierC"]
CATEGORIES = ["Finished Goods", "Components", "Consumables"]
RISK_TIERS = ["Low", "Medium", "High"]


def write_csv(output_dir: Path, name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def generate(output_dir: Path) -> dict[str, int]:
    suppliers = [
        {
            "supplier_id": f"SUP{i:03d}",
            "supplier_name": f"Supplier {i:02d}",
            "base_lead_time_days": 4 + i,
            "supplier_risk_tier": RISK_TIERS[(i - 1) % len(RISK_TIERS)],
        }
        for i in range(1, 7)
    ]
    products = [
        {
            "sku": f"SKU-{i:04d}",
            "product_category": CATEGORIES[(i - 1) % len(CATEGORIES)],
            "supplier_id": suppliers[(i - 1) % len(suppliers)]["supplier_id"],
            "unit_price": f"{18.0 + i * 7.35:.2f}",
            "unit_weight_kg": f"{0.8 + (i % 7) * 1.15:.2f}",
        }
        for i in range(1, 19)
    ]
    customers = [
        {
            "customer_id": f"C{i:04d}",
            "customer_segment": SEGMENTS[(i - 1) % len(SEGMENTS)],
            "region": REGIONS[(i - 1) % len(REGIONS)],
        }
        for i in range(1, 31)
    ]

    order_lines: list[dict[str, object]] = []
    shipments: list[dict[str, object]] = []
    start = date(2025, 1, 3)
    line_no = 1
    for order_no in range(1, 121):
        order_id = f"O{order_no:06d}"
        customer = customers[(order_no * 7) % len(customers)]
        warehouse = WAREHOUSES[(order_no - 1) % len(WAREHOUSES)]
        order_date = start + timedelta(days=(order_no * 3) % 330)
        promised = order_date + timedelta(days=4 + order_no % 4)
        line_count = 1 + order_no % 3
        total_weight = 0.0
        complete = order_no % 5 != 0
        for offset in range(line_count):
            product = products[(order_no * 3 + offset) % len(products)]
            ordered = 4 + ((order_no + offset * 2) % 18)
            shipped = ordered if complete or offset else max(0, ordered - (1 + order_no % 3))
            price = float(product["unit_price"])
            weight = float(product["unit_weight_kg"])
            total_weight += shipped * weight
            order_lines.append(
                {
                    "order_line_id": f"OL{line_no:07d}",
                    "order_id": order_id,
                    "customer_id": customer["customer_id"],
                    "warehouse": warehouse,
                    "order_date": order_date.isoformat(),
                    "promised_date": promised.isoformat(),
                    "sku": product["sku"],
                    "supplier_id": product["supplier_id"],
                    "units_ordered": ordered,
                    "units_shipped": shipped,
                    "unit_price": f"{price:.2f}",
                    "unit_weight_kg": f"{weight:.2f}",
                    "revenue": f"{shipped * price:.2f}",
                }
            )
            line_no += 1
        ship_date = order_date + timedelta(days=1 + order_no % 3)
        delivery = ship_date + timedelta(days=2 + order_no % 7)
        on_time = delivery <= promised
        exception_cost = 0.0 if on_time and complete else round(12.0 + order_no % 9 * 3.5, 2)
        shipments.append(
            {
                "shipment_id": f"S{order_no:06d}",
                "order_id": order_id,
                "carrier": CARRIERS[(order_no - 1) % len(CARRIERS)],
                "warehouse": warehouse,
                "ship_date": ship_date.isoformat(),
                "delivery_date": delivery.isoformat(),
                "promised_date": promised.isoformat(),
                "shipment_weight_kg": f"{total_weight:.2f}",
                "freight_cost": f"{45.0 + total_weight * 0.42:.2f}",
                "handling_cost": f"{8.0 + line_count * 2.25:.2f}",
                "exception_cost": f"{exception_cost:.2f}",
                "on_time": str(on_time),
            }
        )

    inventory: list[dict[str, object]] = []
    forecasts: list[dict[str, object]] = []
    activity: list[dict[str, object]] = []
    for month in range(1, 7):
        month_date = date(2025, month, 1)
        for warehouse_index, warehouse in enumerate(WAREHOUSES):
            units_processed = 900 + month * 45 + warehouse_index * 80
            activity.append(
                {
                    "activity_date": month_date.isoformat(),
                    "warehouse": warehouse,
                    "units_processed": units_processed,
                    "labor_hours": f"{units_processed / (29 + warehouse_index * 2):.2f}",
                }
            )
            for product_index, product in enumerate(products):
                actual = (month * 17 + product_index * 11 + warehouse_index * 7) % 90
                forecast = max(0, actual + ((product_index + month) % 9) - 4)
                demand = actual / 30.0
                on_hand = 0 if (month + product_index + warehouse_index) % 17 == 0 else max(
                    0, int(demand * (5 + product_index % 18))
                )
                inventory.append(
                    {
                        "snapshot_date": month_date.isoformat(),
                        "warehouse": warehouse,
                        "sku": product["sku"],
                        "on_hand_units": on_hand,
                        "average_daily_demand": f"{demand:.3f}",
                        "inventory_value": f"{on_hand * float(product['unit_price']):.2f}",
                    }
                )
                forecasts.append(
                    {
                        "month": month_date.isoformat(),
                        "warehouse": warehouse,
                        "sku": product["sku"],
                        "forecast_units": forecast,
                        "actual_units": actual,
                    }
                )

    files = {
        "suppliers.csv": suppliers,
        "products.csv": products,
        "customers.csv": customers,
        "erp_order_lines.csv": order_lines,
        "tms_shipments.csv": shipments,
        "wms_inventory_snapshots.csv": inventory,
        "demand_forecasts.csv": forecasts,
        "warehouse_activity.csv": activity,
    }
    for name, rows in files.items():
        write_csv(output_dir, name, list(rows[0]), rows)

    return {name: len(rows) for name, rows in files.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/raw")
    args = parser.parse_args()
    print(generate(Path(args.output_dir)))


if __name__ == "__main__":
    main()
