import unittest
from pathlib import Path
import pandas as pd
from src.analytics import analyze, load_data, validate_data

BASE = Path(__file__).resolve().parents[1] / "data"


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.orders = pd.DataFrame([dict(order_id="O1", order_date="2026-07-01", channel="Dine-in", guest_count=2,
                                         discount_amount=5.0)])
        self.items = pd.DataFrame([dict(order_id="O1", line_id="L1", sku="A", quantity=2, unit_price=10.0)])
        self.shifts = pd.DataFrame([dict(shift_id="S1", paid_hours=2.0, hourly_rate=10.0)])
        self.menu = pd.DataFrame([dict(sku="A", item_name="Example Item", category="Test", unit_cost=3.0)])

    def test_order_level_discount_not_multiplied_by_line_count(self):
        r = analyze(self.orders, self.items, self.shifts, self.menu)
        self.assertEqual(r["overview"]["gross_sales"], 20.0)
        self.assertEqual(r["overview"]["net_sales"], 15.0)
        self.assertEqual(r["overview"]["direct_hourly_wages"], 20.0)

    def test_duplicate_ids_are_rejected(self):
        duplicate = pd.concat([self.orders, self.orders], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_data(duplicate, self.items, self.shifts, self.menu)

    def test_unmatched_item_order_is_rejected(self):
        self.items.loc[0, "order_id"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "unknown order"):
            validate_data(self.orders, self.items, self.shifts, self.menu)

    def test_discount_greater_than_order_is_rejected(self):
        self.orders.loc[0, "discount_amount"] = 50.0
        with self.assertRaisesRegex(ValueError, "discounts exceed"):
            validate_data(self.orders, self.items, self.shifts, self.menu)

    def test_missing_cost_does_not_generate_partial_contribution_claim(self):
        self.menu.loc[0, "unit_cost"] = float("nan")
        r = analyze(self.orders, self.items, self.shifts, self.menu)
        self.assertIsNone(r["overview"]["modeled_contribution_after_known_cogs_and_hourly_wages"])
        self.assertFalse(r["overview"]["full_menu_cost_coverage"])

    def test_shipped_sample_passes_validation(self):
        r = analyze(*load_data(BASE))
        self.assertTrue(r["is_synthetic"])
        self.assertGreater(r["overview"]["transactions"], 500)
        self.assertAlmostEqual(r["overview"]["gross_sales"] - r["overview"]["discounts"],
                               r["overview"]["net_sales"], places=2)
        self.assertGreater(r["overview"]["dine_in_missing_cover_orders"], 0)


if __name__ == "__main__":
    unittest.main()
