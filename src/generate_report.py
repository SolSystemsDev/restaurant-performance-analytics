"""Generate self-contained HTML and JSON reports from the synthetic CSV files."""
from __future__ import annotations
import json
from html import escape
from pathlib import Path
from .analytics import analyze, load_data

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def money(value: float | None) -> str:
    return "N/A" if value is None else f"${value:,.2f}"


def pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:,.1f}%"


def make_html(report: dict) -> str:
    overview = report["overview"]
    metrics = [
        ("Net sales", money(overview["net_sales"]), "Gross minus order-level discounts"),
        ("Transactions", f'{overview["transactions"]:,}', "One transaction per order"),
        ("Average net check", money(overview["average_transaction_net"]), "Net sales ÷ orders"),
        ("Discount rate", pct(overview["discount_rate_pct"]), "Discounts ÷ gross sales"),
        ("Sales / labor hour", money(overview["sales_per_paid_labor_hour"]), "Net sales ÷ paid hours"),
        ("Direct wage rate", pct(overview["wage_cost_pct_net_sales"]), "Hourly wages ÷ net sales"),
        ("Menu cost coverage", pct(overview["cost_coverage_by_gross_sales_pct"]), "Share of gross sales with known item costs"),
        ("Known-item COGS", money(overview["known_item_cogs_partial"]), "Partial cost total — not full COGS"),
    ]
    cards = "".join(f'<section class="metric"><small>{escape(label)}</small><strong>{escape(value)}</strong><span>{escape(note)}</span></section>'
                    for label, value, note in metrics)
    total_sales = max(1.0, overview["net_sales"])
    channels = "".join(
        f'<div class="bar-row"><div><b>{escape(x["channel"])}</b><span>{x["orders"]} orders · {money(x["net_sales"])}</span></div>'
        f'<div class="bar-track"><div class="bar" style="width:{x["net_sales"] / total_sales * 100:.1f}%"></div></div></div>'
        for x in report["channels"])
    top_rows = "".join(f'<tr><td>{escape(x["item"])}</td><td>{x["units"]}</td><td>{money(x["gross_sales"])}</td></tr>'
                       for x in report["top_items"])
    alerts = "".join(f'<li>{escape(w)}</li>' for w in report["warnings"])
    # Lightweight SVG sparkline; values are illustrative and dates are displayed above.
    amounts = [x["net_sales"] for x in report["daily"]]
    low, high = min(amounts), max(amounts)
    denom = max(high - low, 1)
    points = " ".join(f'{i*700/max(len(amounts)-1,1):.1f},{140-(v-low)/denom*125:.1f}' for i, v in enumerate(amounts))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Restaurant Analytics · Fictional Portfolio Demo</title>
<style>
:root{{--ink:#132437;--sub:#64748b;--blue:#2563eb;--line:#dce4ed;--bg:#f4f7fb}}
*{{box-sizing:border-box}}body{{margin:0;font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;color:var(--ink);background:var(--bg)}}
header{{background:#102642;color:white;padding:35px max(20px,calc((100vw - 1000px)/2))}}header h1{{font-size:clamp(22px,4vw,34px);margin:8px 0}}header p{{color:#c8d7e6;margin:0}}
.badge{{display:inline-block;background:#ebae42;color:#172337;font-weight:800;padding:5px 12px;border-radius:50px;font-size:12px}}
main{{max-width:1040px;margin:0 auto;padding:25px 20px 60px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}}
.metric,.panel{{background:white;border:1px solid var(--line);border-radius:13px;box-shadow:0 2px 8px #16345309}}
.metric{{padding:18px;min-height:145px}}small{{font-weight:700;color:var(--sub);text-transform:uppercase;letter-spacing:.04em}}
.metric strong{{display:block;font-size:27px;margin:8px 0}}.metric span{{color:var(--sub);font-size:12px}}
.panel{{padding:22px;margin-top:18px}}h2{{margin:0 0 15px;font-size:21px}}h3{{font-size:15px;margin:16px 0 8px}}
.bar-row{{margin:16px 0}}.bar-row>div:first-child{{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}.bar-row span{{color:var(--sub)}}.bar-track{{height:12px;background:#e9f0fa;border-radius:99px;margin-top:7px;overflow:hidden}}
.bar{{height:100%;background:#2563eb;border-radius:99px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px 5px;border-bottom:1px solid var(--line);text-align:left}}th{{color:var(--sub)}}
svg{{width:100%;height:180px}}.warning{{background:#fff9ec;border-left:4px solid #df9a28}}.warning li{{margin:7px 0}}
footer{{color:var(--sub);margin-top:20px;font-size:12px}}
</style></head>
<body><header><span class="badge">FICTIONAL / SYNTHETIC DATA</span><h1>Restaurant Performance Snapshot</h1>
<p>SolSystemsDev · Illustrative analytics portfolio · {report["period_start"]} to {report["period_end"]}</p></header>
<main><div class="grid">{cards}</div>
<section class="panel"><h2>Daily net sales</h2><svg viewBox="0 0 710 165" role="img" aria-label="Trend of daily net sales"><polyline points="{points}" fill="none" stroke="#2563eb" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/></svg><small>28-day fictional sample · net of order-level discounts</small></section>
<section class="panel"><h2>Revenue by channel</h2>{channels}</section>
<section class="panel"><h2>Top five menu items by gross sales</h2><table><thead><tr><th>Item</th><th>Units</th><th>Gross sales</th></tr></thead><tbody>{top_rows}</tbody></table></section>
<section class="panel warning"><h2>Data quality and interpretation</h2><ul>{alerts}</ul>
<p>Net sales exclude taxes, tips and platform fees. Labor cost represents modeled hourly wages only; no payroll taxes, benefits, occupancy or overhead are included. This is not a profit-and-loss statement.</p></section>
<footer>Reproduce: <code>python -m src.generate_report</code> · Methodology: <code>docs/methodology.md</code> · All records are generated and do not represent a real restaurant.</footer></main></body></html>'''


def main() -> None:
    r = analyze(*load_data())
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "sample_metrics.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
    (REPORTS / "sample_performance_report.html").write_text(make_html(r), encoding="utf-8")
    print("Generated:", REPORTS / "sample_performance_report.html")
    print("Net sales:", money(r["overview"]["net_sales"]), "|", r["overview"]["transactions"], "transactions")
    print("Warnings:", len(r["warnings"]))


if __name__ == "__main__":
    main()
