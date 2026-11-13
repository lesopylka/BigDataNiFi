import os
import requests


BASE = "http://metabase:3000/api"


def main():
    session = requests.Session()
    response = session.post(BASE + "/session", json={
        "username": os.environ["MB_EMAIL"], "password": os.environ["MB_PASSWORD"],
    }, timeout=60)
    response.raise_for_status()
    session.headers["X-Metabase-Session"] = response.json()["id"]
    response = session.get(BASE + "/dashboard", timeout=60)
    response.raise_for_status()
    dashboards = response.json()
    if isinstance(dashboards, dict):
        dashboards = dashboards["data"]
    dashboard = next(item for item in dashboards if item["name"] == "Лабораторная работа 5")
    response = session.get(BASE + f"/dashboard/{dashboard['id']}", timeout=60)
    response.raise_for_status()
    cards = [card["card"] for card in response.json()["dashcards"] if card.get("card")]
    assert len(cards) == 22, f"Expected 22 cards, got {len(cards)}"
    for card in cards:
        response = session.post(BASE + f"/card/{card['id']}/query", json={}, timeout=120)
        response.raise_for_status()
        result = response.json()
        assert result.get("status") == "completed", (card["name"], result)
        assert result["data"]["rows"], card["name"]
        print(card["name"], "OK", flush=True)
    print("All 22 Metabase cards executed successfully")


if __name__ == "__main__":
    main()
