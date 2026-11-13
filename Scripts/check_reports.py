import csv
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def check_reports(reports, directory=Path("data")):
    rows = []
    for path in sorted(directory.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as source:
            rows.extend(csv.DictReader(source))
    if len(rows) != 10000:
        raise ValueError(f"Ожидалось 10000 продаж, получено {len(rows)}")

    for table, field, price, metric in [
        ("stores", "store_name", "sale_total_price", "average_order"),
        ("suppliers", "supplier_name", "product_price", "average_price"),
    ]:
        revenue = defaultdict(Decimal)
        prices = defaultdict(list)
        for row in rows:
            revenue[row[field]] += Decimal(row["sale_total_price"])
            prices[row[field]].append(Decimal(row[price]))
        expected_top = sorted(revenue, key=lambda name: (-revenue[name], name))[:5]
        actual_top = sorted([row for row in reports[table] if row["metric"] == "top_revenue"], key=lambda row: (-row["value"], row["entity"]))
        assert [row["entity"] for row in actual_top] == expected_top, table
        for row in actual_top:
            assert abs(row["value"] - float(revenue[row["entity"]])) < 0.000001, row
        averages = {row["entity"]: row["value"] for row in reports[table] if row["metric"] == metric}
        assert averages.keys() == prices.keys(), (table, "Неверные группы")
        for name, values in prices.items():
            assert abs(averages[name] - float(sum(values) / len(values))) < 0.000001, (table, name)

    periods = defaultdict(list)
    years = defaultdict(list)
    for row in rows:
        date = datetime.strptime(row["sale_date"], "%m/%d/%Y")
        amount = Decimal(row["sale_total_price"])
        periods[date.strftime("%Y-%m")].append(amount)
        years[date.strftime("%Y")].append(amount)
    for metric, groups, average in [("month_revenue", periods, False), ("year_revenue", years, False), ("month_average_order", periods, True)]:
        actual = {row["period"]: row["value"] for row in reports["time"] if row["metric"] == metric}
        assert actual.keys() == groups.keys(), metric
        for period, values in groups.items():
            expected = sum(values) / len(values) if average else sum(values)
            assert abs(actual[period] - float(expected)) < 0.000001, (metric, period)
    for metric, groups in [("month_revenue_change", periods), ("year_revenue_change", years)]:
        actual = {row["period"]: row.get("value") for row in reports["time"] if row["metric"] == metric}
        assert actual.keys() == groups.keys(), metric
        previous = None
        for period in sorted(groups):
            current = sum(groups[period])
            if previous is None:
                assert actual[period] is None, (metric, period)
            else:
                assert abs(actual[period] - float(current - previous)) < 0.000001, (metric, period)
            previous = current
    print("Топы, средние и временные показатели совпадают с CSV")
