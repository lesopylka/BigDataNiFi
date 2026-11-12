import os
import time
import requests


BASE = "http://metabase:3000/api"
SESSION = requests.Session()


def api(method, path, payload=None):
    response = SESSION.request(method, BASE + path, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def main():
    for attempt in range(120):
        try:
            properties = api("GET", "/session/properties")
            break
        except requests.RequestException:
            time.sleep(5)
    else:
        raise RuntimeError("Metabase не запустился")
    email = os.environ["MB_EMAIL"]
    password = os.environ["MB_PASSWORD"]
    if properties.get("setup-token"):
        api("POST", "/setup", {
            "token": properties["setup-token"],
            "user": {"first_name": "Alina", "last_name": "Sulyaeva", "email": email, "password": password},
            "prefs": {"site_name": "Анализ продаж", "site_locale": "ru", "allow_tracking": False},
        })
    session = api("POST", "/session", {"username": email, "password": password})
    SESSION.headers["X-Metabase-Session"] = session["id"]
    databases = api("GET", "/database")["data"]
    db = next((item for item in databases if item["name"] == "sales"), None)
    if db is None:
        db = api("POST", "/database", {"name": "sales", "engine": "postgres", "details": {
            "host": "postgres", "port": 5432, "dbname": "postgres", "user": "postgres", "password": "postgres", "ssl": False,
        }})
    dashboards = api("GET", "/dashboard")
    if any(item["name"] == "Лабораторная работа 5" for item in dashboards):
        print("Дашборд уже существует")
        return
    dashboard = api("POST", "/dashboard", {"name": "Лабораторная работа 5", "description": "Продажи, клиенты, магазины, поставщики и качество товаров"})
    charts = [
        ("Топ-10 товаров", "products", "top_quantity", "bar"),
        ("Выручка по категориям", "products", "category_revenue", "bar"),
        ("Рейтинги товаров", "products", "average_rating", "bar"),
        ("Отзывы по товарам", "products", "reviews", "bar"),
        ("Топ-10 клиентов", "customers", "top_revenue", "bar"),
        ("Клиенты по странам", "customers", "country_customers", "bar"),
        ("Средний чек клиента", "customers", "average_order", "table"),
        ("Выручка по месяцам", "time", "month_revenue", "line"),
        ("Выручка по годам", "time", "year_revenue", "bar"),
        ("Изменение выручки", "time", "month_revenue_change", "line"),
        ("Средний чек по месяцам", "time", "month_average_order", "line"),
        ("Топ-5 магазинов", "stores", "top_revenue", "bar"),
        ("Города магазинов", "stores", "city_revenue", "table"),
        ("Страны магазинов", "stores", "country_revenue", "bar"),
        ("Средний чек магазина", "stores", "average_order", "table"),
        ("Топ-5 поставщиков", "suppliers", "top_revenue", "bar"),
        ("Средняя цена поставщика", "suppliers", "average_price", "table"),
        ("Страны поставщиков", "suppliers", "country_revenue", "bar"),
        ("Лучшие рейтинги", "quality", "highest_rating", "bar"),
        ("Худшие рейтинги", "quality", "lowest_rating", "bar"),
        ("Больше всего отзывов", "quality", "most_reviews", "bar"),
        ("Корреляция рейтинга и продаж", "quality", "rating_quantity_correlation", "scalar"),
    ]
    cards = []
    for index, (title, report, metric, display) in enumerate(charts):
        axis = "period" if report == "time" else "entity"
        query = f"SELECT {axis}, value FROM public.report_{report} WHERE metric = '{metric}' ORDER BY "
        query += "period" if report == "time" else "value DESC NULLS LAST, entity"
        card = api("POST", "/card", {"name": title, "display": display,
            "dataset_query": {"type": "native", "database": db["id"], "native": {"query": query}},
            "visualization_settings": {"graph.dimensions": [axis], "graph.metrics": ["value"]},
        })
        cards.append({"id": -(index + 1), "card_id": card["id"], "row": (index // 2) * 5,
                      "col": (index % 2) * 12, "size_x": 12, "size_y": 5, "parameter_mappings": []})
    api("PUT", f"/dashboard/{dashboard['id']}/cards", {"cards": cards})
    print(f"Дашборд готов: http://localhost:3000/dashboard/{dashboard['id']}")


if __name__ == "__main__":
    main()
