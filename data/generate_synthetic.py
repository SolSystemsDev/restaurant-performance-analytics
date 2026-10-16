"""Create deterministic, 100% fictional restaurant data for portfolio demonstrations."""
from __future__ import annotations
import csv
import random
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
SEED = 1701
MENU = [
    ("S01", "Salmon Roll", "Sushi", 14.00, 4.10),
    ("S02", "Spicy Tuna Roll", "Sushi", 15.00, 4.85),
    ("S03", "California Roll", "Sushi", 11.00, 3.15),
    ("S04", "Dragon Roll", "Specialty Sushi", 19.00, 6.20),
    ("S05", "Rainbow Roll", "Specialty Sushi", 20.00, 7.35),
    ("S06", "Gyoza", "Appetizer", 8.00, 2.05),
    ("S07", "Chicken Teriyaki", "Kitchen", 18.00, ""),  # intentional cost gap
    ("S08", "Shrimp Tempura", "Kitchen", 17.00, 5.90),
    ("S09", "Miso Soup", "Side", 4.00, 0.85),
    ("S10", "Green Tea", "Beverage", 3.50, 0.35),
]


def write_csv(name: str, header: list[str], rows: list[dict]) -> None:
    path = BASE / name
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def build() -> dict[str, int]:
    rng = random.Random(SEED)
    prices = {m[0]: m[3] for m in MENU}
    orders, items, shifts = [], [], []
    start = date(2026, 7, 1)
    n_order, n_line, n_shift = 0, 0, 0
    for i in range(28):
        d = start + timedelta(days=i)
        weekend = d.weekday() in (4, 5, 6)
        count = rng.randint(55, 84) if weekend else rng.randint(32, 61)
        for _ in range(count):
            n_order += 1
            oid = f"ORD{n_order:05d}"
            channel = rng.choices(["Dine-in", "Pickup", "Delivery"], [0.64, 0.19, 0.17])[0]
            daypart = rng.choices(["Lunch", "Dinner"], [0.42, 0.58])[0]
            hour = rng.randint(11, 14) if daypart == "Lunch" else rng.randint(17, 21)
            minute = rng.randint(0, 59)
            # Covers are not appropriate for pickup/delivery; intentional blanks for 5% dine-in.
            covers = rng.randint(1, 5) if channel == "Dine-in" and rng.random() >= 0.05 else ""
            n_items = rng.choices([1, 2, 3, 4], [0.25, 0.43, 0.25, 0.07])[0]
            line_total = 0.0
            for _ in range(n_items):
                sku = rng.choices([m[0] for m in MENU], [13, 13, 11, 9, 8, 8, 11, 8, 10, 9])[0]
                qty = rng.choices([1, 2, 3], [0.74, 0.21, 0.05])[0]
                price = prices[sku]
                n_line += 1
                items.append(dict(order_id=oid, line_id=f"LINE{n_line:06d}", sku=sku, quantity=qty, unit_price=f"{price:.2f}"))
                line_total += qty * price
            promotion = rng.choices(["None", "Happy Hour", "Voucher"], [0.77, 0.17, 0.06])[0]
            discount = 0.0
            if promotion == "Happy Hour":
                discount = round(line_total * 0.12, 2)
            elif promotion == "Voucher" and line_total >= 25:
                discount = min(12.0, round(line_total * 0.30, 2))
            orders.append(dict(order_id=oid, order_date=d.isoformat(), order_time=f"{hour:02d}:{minute:02d}",
                               daypart=daypart, channel=channel, guest_count=covers,
                               promotion=promotion, discount_amount=f"{discount:.2f}"))
        # Cost here is modeled *direct hourly wages only*, not total loaded labor expense.
        staffing = [("Server", 2, 7.0, 8.0), ("Sushi chef", 2, 8.0, 17.0),
                    ("Cook", 2, 8.0, 16.0), ("Host", 1, 6.0, 11.0)]
        if weekend:
            staffing.extend([("Server", 1, 5.0, 8.0), ("Host", 1, 5.0, 11.0)])
        for role, people, hours, rate in staffing:
            for _ in range(people):
                n_shift += 1
                shifts.append(dict(shift_id=f"SH{n_shift:05d}", shift_date=d.isoformat(),
                                   role=role, paid_hours=f"{hours:.2f}", hourly_rate=f"{rate:.2f}"))
    write_csv("menu_costs.csv", ["sku", "item_name", "category", "unit_cost"],
              [dict(sku=sku, item_name=name, category=cat, unit_cost=cost)
               for sku, name, cat, _, cost in MENU])
    write_csv("orders.csv", ["order_id", "order_date", "order_time", "daypart", "channel", "guest_count", "promotion", "discount_amount"], orders)
    write_csv("order_items.csv", ["order_id", "line_id", "sku", "quantity", "unit_price"], items)
    write_csv("labor_shifts.csv", ["shift_id", "shift_date", "role", "paid_hours", "hourly_rate"], shifts)
    return {"orders": len(orders), "order_items": len(items), "labor_shifts": len(shifts)}


if __name__ == "__main__":
    print("Generated fictional demo data:", build())
