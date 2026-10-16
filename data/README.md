# Synthetic dataset and data dictionary

**These are fabricated examples** produced deterministically by `python data/generate_synthetic.py`. They do not originate from any employer, customer, restaurant, or payment processor. Dates are fictional examples covering 28 days in July 2026.

| File | One row per | Important fields |
|---|---|---|
| `orders.csv` | order | `order_id`, `order_date`, `channel`, `guest_count`, `promotion`, `discount_amount` |
| `order_items.csv` | purchased line | `line_id`, `order_id`, `sku`, `quantity`, `unit_price` |
| `menu_costs.csv` | menu SKU | `sku`, `item_name`, `category`, `unit_cost` |
| `labor_shifts.csv` | modeled paid shift | `shift_id`, `shift_date`, `role`, `paid_hours`, `hourly_rate` |

**Data quality intentionally demonstrated:** `S07` has an unknown unit recipe cost; a small proportion of dine-in orders lack cover counts; pickup and delivery orders have no covers by design.

Prices and costs are illustrative, not representative of a specific restaurant. Order promotions/discounts are synthetic and not a simulation of specific historical voucher settlements, platform commissions, taxes, gratuities or payments.
