# Methodology — v0.1

## Source and purpose

All observations are **synthetic and deterministic**. This exercise demonstrates data validation, transaction-grain reporting, SQL, Pandas, and management reporting. It does not provide insights about an actual operating restaurant.

## KPI definitions

| KPI | Computation | Limit |
|---|---|---|
| Gross sales | Sum of `order_items.quantity × unit_price` | Pre-discount, excludes tax/tips |
| Discounts | One `orders.discount_amount` per order | **Never** join and sum discount at item-line grain |
| Net sales | Gross sales minus discounts | Excludes tax, tips, platform processing, delivery service fees |
| Transactions | Distinct order IDs | Not individual customer count |
| Average net check | Net sales / transactions | Includes all channels |
| Paid labor hours | Sum of modeled `paid_hours` | Excludes unpaid hours and productivity breakdown |
| Direct hourly wages | Sum of `paid_hours × hourly_rate` | Excludes taxes, benefits, tips, salaried management |
| Sales / paid labor hour | Net sales / paid labor hours | Not an effectiveness score without service context |
| Direct wage % of net sales | Direct hourly wages / net sales | Not fully loaded labor percentage |
| Known-item COGS | Sum of sold units × unit cost where known | **Partial** when even one sold SKU cost missing |
| Menu cost coverage | Gross sales of items with known cost / gross sales | Coverage is **sales weighted**, not percent of SKUs |

The script deliberately does not report a total contribution figure when sold menu items lack unit costs. Even with complete menu costs, net sales minus menu cost minus direct wages would be a limited modeled **contribution proxy**, never net profit.

## Data-quality checks

- Unique primary keys: order ID, line ID, shift ID, SKU.
- Orphan order items or unknown SKU relationships are errors.
- Negative or missing prices, quantities, discounts, paid hours, and hourly wage rates are errors.
- Discounts cannot exceed order gross value.
- Guest counts may be blank; zero/negative known guest counts are invalid.
- Unknown menu costs and missing dine-in cover counts are disclosed as warnings.

## Validation and replication

```bash
pip install -r requirements.txt
python data/generate_synthetic.py
python -m unittest discover -s tests -v
python -m src.generate_report
python -m src.load_sqlite
```

Generated report: `reports/sample_performance_report.html`.

## Potential enhancements

1. Include shift-level coverage vs. order arrival curves.
2. Add a reservation/covers quality screen and coverage-aware per-cover KPIs.
3. Incorporate platform settlement data separately from face-value promotions.
4. Add recipe-level costs with effective dates and actual payroll burden.
5. Expose a versioned validation manifest and more regression test fixtures.

This is a portfolio demo and is not validated against customer production data.
