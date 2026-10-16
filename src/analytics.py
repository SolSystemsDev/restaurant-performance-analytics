"""Restaurant KPI pipeline: validate at the correct transaction/line/shift grains."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_data(data_dir: Path = DATA_DIR) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    orders = pd.read_csv(data_dir / "orders.csv", dtype={"order_id": "string", "channel": "string"})
    items = pd.read_csv(data_dir / "order_items.csv", dtype={"order_id": "string", "sku": "string"})
    shifts = pd.read_csv(data_dir / "labor_shifts.csv")
    menu = pd.read_csv(data_dir / "menu_costs.csv", dtype={"sku": "string"})
    return orders, items, shifts, menu


def validate_data(orders: pd.DataFrame, items: pd.DataFrame, shifts: pd.DataFrame, menu: pd.DataFrame) -> list[str]:
    """Raise ValueError for broken monetary joins; report missing coverage as warnings."""
    errors: list[str] = []
    for label, df, key in [("orders", orders, "order_id"), ("items", items, "line_id"),
                           ("shifts", shifts, "shift_id"), ("menu", menu, "sku")]:
        if df[key].isna().any() or df[key].duplicated().any():
            errors.append(f"{label}: {key} must be present and unique")
    if not items["order_id"].isin(orders["order_id"]).all():
        errors.append("Item lines contain unknown order IDs")
    if not items["sku"].isin(menu["sku"]).all():
        errors.append("Item lines contain SKUs missing from menu catalog")
    for label, frame, cols in [("items", items, ["quantity", "unit_price"]),
                               ("orders", orders, ["discount_amount"]),
                               ("shifts", shifts, ["paid_hours", "hourly_rate"])]:
        for col in cols:
            if frame[col].isna().any() or (frame[col] < 0).any():
                errors.append(f"{label}.{col} contains invalid values")
    if (items["quantity"] <= 0).any():
        errors.append("items.quantity must be greater than zero")
    bad_covers = orders["guest_count"].notna() & (orders["guest_count"] <= 0)
    if bad_covers.any():
        errors.append("Known guest_count must be positive; unknown covers must be blank")
    per_order_gross = items.assign(ext=items["quantity"] * items["unit_price"]).groupby("order_id")["ext"].sum()
    if (orders["discount_amount"].to_numpy() > orders["order_id"].map(per_order_gross).fillna(0).to_numpy() + 0.001).any():
        errors.append("Order discounts exceed order gross value, or an order has no item lines")
    if errors:
        raise ValueError("Data validation failed: " + "; ".join(errors))

    warnings: list[str] = []
    if menu["unit_cost"].isna().any():
        warnings.append("Some menu items lack unit costs. Known-item COGS is partial; no overall contribution margin is reported.")
    dine = orders[orders["channel"] == "Dine-in"]
    if dine["guest_count"].isna().any():
        warnings.append("Some dine-in transactions have unknown covers. Revenue per guest is not computed.")
    return warnings


def analyze(orders: pd.DataFrame, items: pd.DataFrame, shifts: pd.DataFrame, menu: pd.DataFrame) -> dict:
    warnings = validate_data(orders, items, shifts, menu)
    work_items = items.merge(menu[["sku", "item_name", "category", "unit_cost"]], on="sku", validate="many_to_one")
    work_items["gross_line"] = work_items["quantity"] * work_items["unit_price"]
    work_items["known_cogs_line"] = work_items["quantity"] * work_items["unit_cost"]
    gross_per_order = work_items.groupby("order_id", as_index=False)["gross_line"].sum()
    tx = orders.merge(gross_per_order, on="order_id", validate="one_to_one")
    tx["net_sales"] = tx["gross_line"] - tx["discount_amount"]
    gross = float(work_items["gross_line"].sum())
    discounts = float(orders["discount_amount"].sum())
    net = float(tx["net_sales"].sum())
    hours = float(shifts["paid_hours"].sum())
    wage_cost = float((shifts["paid_hours"] * shifts["hourly_rate"]).sum())
    cost_covered_gross = float(work_items.loc[work_items["unit_cost"].notna(), "gross_line"].sum())
    coverage_pct = 100 * cost_covered_gross / gross if gross > 0 else 0
    all_costs_known = bool(work_items["unit_cost"].notna().all())
    known_cogs = float(work_items["known_cogs_line"].sum())
    by_channel = (tx.groupby("channel").agg(orders=("order_id", "count"), net_sales=("net_sales", "sum"))
                  .reset_index().sort_values("net_sales", ascending=False))
    daily = (tx.groupby("order_date").agg(orders=("order_id", "count"), net_sales=("net_sales", "sum"))
             .reset_index().sort_values("order_date"))
    by_item = (work_items.groupby(["sku", "item_name"], as_index=False)
               .agg(units=("quantity", "sum"), gross_sales=("gross_line", "sum"))
               .sort_values("gross_sales", ascending=False).head(5))
    dine = orders[orders["channel"] == "Dine-in"]
    return {
        "period_start": str(tx["order_date"].min()), "period_end": str(tx["order_date"].max()),
        "is_synthetic": True,
        "overview": {
            "transactions": int(len(tx)), "gross_sales": round(gross, 2),
            "discounts": round(discounts, 2), "net_sales": round(net, 2),
            "average_transaction_net": round(net / len(tx), 2) if len(tx) else None,
            "discount_rate_pct": round(100 * discounts / gross, 2) if gross else None,
            "paid_labor_hours": round(hours, 2), "direct_hourly_wages": round(wage_cost, 2),
            "sales_per_paid_labor_hour": round(net / hours, 2) if hours else None,
            "wage_cost_pct_net_sales": round(100 * wage_cost / net, 2) if net else None,
            "known_item_cogs_partial": round(known_cogs, 2),
            "cost_coverage_by_gross_sales_pct": round(coverage_pct, 2),
            "full_menu_cost_coverage": all_costs_known,
            "modeled_contribution_after_known_cogs_and_hourly_wages": round(net - known_cogs - wage_cost, 2) if all_costs_known else None,
            "dine_in_missing_cover_orders": int(dine["guest_count"].isna().sum()),
            "dine_in_orders": int(len(dine)),
        },
        "channels": [{"channel": str(r.channel), "orders": int(r.orders), "net_sales": round(float(r.net_sales), 2)}
                     for r in by_channel.itertuples()],
        "daily": [{"date": str(r.order_date), "orders": int(r.orders), "net_sales": round(float(r.net_sales), 2)}
                  for r in daily.itertuples()],
        "top_items": [{"sku": str(r.sku), "item": str(r.item_name), "units": int(r.units), "gross_sales": round(float(r.gross_sales), 2)}
                      for r in by_item.itertuples()],
        "warnings": warnings,
    }
