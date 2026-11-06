from datetime import date
from tests.conftest import EVENTS

CATEGORIES = ["식비", "교통비", "쇼핑", "주거비", "생활비"]

def payload(i, kind):
    return {"type": kind, "date": f"{date.today().year}-{date.today().month:02d}-{(i % 28) + 1:02d}", "amount": (i + 1) * 1000, "category": "급여" if kind == "income" else CATEGORIES[i % len(CATEGORIES)], "memo": f"synthetic-{kind}-{i}"}

def test_register_30_income_70_expense_and_summary(request_json):
    created = []
    for i in range(30):
        response = request_json("post", "/api/transactions", json=payload(i, "income")); assert response.status_code == 201; created.append(response.json())
    for i in range(70):
        response = request_json("post", "/api/transactions", json=payload(i, "expense")); assert response.status_code == 201; created.append(response.json())
    assert len(created) == 100
    summary = request_json("get", "/api/summary").json()
    assert summary["total_income"] == sum(payload(i, "income")["amount"] for i in range(30))
    assert summary["total_expense"] == sum(payload(i, "expense")["amount"] for i in range(70))
    assert summary["balance"] == summary["total_income"] - summary["total_expense"]
    assert sum(x["amount"] for x in summary["categories"]) == summary["total_expense"]
    assert summary["month_income"] == summary["total_income"]
    assert summary["month_expense"] == summary["total_expense"]
    assert sum(x["amount"] for x in summary["months"]) == summary["total_income"] + summary["total_expense"]

def test_list_filters_update_delete(request_json):
    rows = request_json("get", "/api/transactions").json(); assert len(rows) == 100
    food = request_json("get", "/api/transactions?category=식비").json(); assert food and all(x["category"] == "식비" for x in food)
    target = rows[0]; updated = {**payload(99, "expense"), "memo": "updated-synthetic"}
    response = request_json("put", f"/api/transactions/{target['id']}", json=updated); assert response.status_code == 200 and response.json()["memo"] == "updated-synthetic"
    assert request_json("delete", f"/api/transactions/{target['id']}").status_code == 200
    assert not any(x["id"] == target["id"] for x in request_json("get", "/api/transactions").json())

def test_invalid_inputs(request_json):
    base = payload(1, "expense")
    invalid = [{**base, "amount": -1}, {**base, "date": "not-a-date"}, {**base, "category": ""}, {k: v for k, v in base.items() if k != "amount"}]
    for item in invalid: assert request_json("post", "/api/transactions", json=item).status_code == 422

def test_bulk_query_performance(request_json):
    response = request_json("get", "/api/transactions"); assert response.status_code == 200 and len(response.json()) == 99
    event = next(e for e in EVENTS if e["path"] == "/api/transactions")
    assert event["response_ms"] < 1000
