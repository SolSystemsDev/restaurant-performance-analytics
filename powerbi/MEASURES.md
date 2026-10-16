# Power BI / DAX examples (not a packaged PBIX)

Import `orders.csv`, `order_items.csv`, `menu_costs.csv`, and `labor_shifts.csv`.
Model `orders[order_id]` (one) → `order_items[order_id]` (many); `menu_costs[sku]` (one) → `order_items[sku]` (many).
Keep labor independent; use a separate shared Date dimension when adding date filters across tables.

```dax
Gross Sales =
SUMX ( order_items, order_items[quantity] * order_items[unit_price] )

Order Discounts =
SUM ( orders[discount_amount] )

Net Sales =
[Gross Sales] - [Order Discounts]

Transactions =
DISTINCTCOUNT ( orders[order_id] )

Average Net Check =
DIVIDE ( [Net Sales], [Transactions] )

Paid Labor Hours =
SUM ( labor_shifts[paid_hours] )

Direct Hourly Wages =
SUMX ( labor_shifts, labor_shifts[paid_hours] * labor_shifts[hourly_rate] )

Sales Per Paid Labor Hour =
DIVIDE ( [Net Sales], [Paid Labor Hours] )

Direct Wages % Net Sales =
DIVIDE ( [Direct Hourly Wages], [Net Sales] )
```

**Modeling caution:** For channel/date-filtered visuals, test filter propagation so discounts and gross sales are filtered consistently. A shared Date table and carefully defined relationships are needed for production-like cross-table reporting.

**No profit or overall food-cost measure is provided:** the synthetic menu intentionally contains a missing recipe cost. Do not infer full margin from partial known costs. All values are fictional.
