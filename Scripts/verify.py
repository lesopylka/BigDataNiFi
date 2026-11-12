import json
import time
from decimal import Decimal
from pathlib import Path
import psycopg
import requests


def main():
    expected = json.loads(Path("expected.json").read_text())
    with psycopg.connect("host=postgres dbname=postgres user=postgres password=postgres") as conn:
        for attempt in range(180):
            row = conn.execute("SELECT COUNT(*), COUNT(DISTINCT sale_key), SUM(sale_quantity::INTEGER), SUM(sale_total_price::NUMERIC(18,2)) FROM public.mock_data").fetchone()
            if row[0] == expected["sales_count"]:
                break
            time.sleep(2)
        assert row == (expected["sales_count"], expected["unique_sales"], expected["total_quantity"], Decimal(expected["total_amount"])), row
        for name in ["products", "customers", "time", "stores", "suppliers", "quality"]:
            assert conn.execute(f"SELECT COUNT(*) FROM public.report_{name}").fetchone()[0] > 0
    print("Количество продаж, ключи, количество товара и сумма совпадают с исходными данными")


if __name__ == "__main__":
    main()
