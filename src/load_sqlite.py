"""Optional: load CSV tables into local SQLite so the SQL examples can be executed."""
import sqlite3
from pathlib import Path
from .analytics import load_data

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    orders, items, shifts, menu = load_data()
    database = ROOT / "data" / "restaurant_demo.sqlite"
    with sqlite3.connect(database) as con:
        for name, df in [("orders", orders), ("order_items", items), ("labor_shifts", shifts), ("menu_costs", menu)]:
            df.to_sql(name, con, if_exists="replace", index=False)
    print("Created", database, "(ignored by Git)")


if __name__ == "__main__":
    main()
