import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

VALID_ORDER = {
    "order_id": "TEST001",
    "category": "fashion",
    "payment_method": "cod",
    "order_value": 2400,
    "discount_pct": 55,
    "customer_tenure_days": 5,
    "customer_past_orders": 1,
    "customer_past_returns": 1,
    "seller_rating": 3.6,
    "delivery_days": 6,
    "promised_delivery_days": 3,
    "is_weekend_purchase": 1,
    "hour_of_day": 23,
    "distance_km": 340,
}

LOW_RISK_ORDER = {
    "order_id": "TEST002",
    "category": "grocery",
    "payment_method": "prepaid_card",
    "order_value": 400,
    "discount_pct": 0,
    "customer_tenure_days": 900,
    "customer_past_orders": 40,
    "customer_past_returns": 0,
    "seller_rating": 4.9,
    "delivery_days": 2,
    "promised_delivery_days": 2,
    "is_weekend_purchase": 0,
    "hour_of_day": 11,
    "distance_km": 15,
}


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_metrics_shape():
    r = client.get("/api/v1/metrics")
    assert r.status_code == 200
    body = r.json()
    assert "headline" in body
    assert "cost_curve" in body
    assert "pr_curve" in body
    assert "feature_importance" in body
    assert 0 <= body["headline"]["precision_at_threshold"] <= 1
    assert 0 <= body["headline"]["recall_at_threshold"] <= 1


def test_predict_single_high_risk_order():
    r = client.post("/api/v1/predict", json=VALID_ORDER)
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["risk_score"] <= 1
    assert body["risk_tier"] in {"low", "medium", "high"}
    assert len(body["reason_codes"]) >= 1


def test_predict_ranks_high_risk_above_low_risk():
    """The core sanity check: a COD/high-discount/poor-history order must
    score meaningfully higher than a prepaid/loyal-customer/grocery order."""
    r_high = client.post("/api/v1/predict", json=VALID_ORDER).json()
    r_low = client.post("/api/v1/predict", json=LOW_RISK_ORDER).json()
    assert r_high["risk_score"] > r_low["risk_score"]


def test_predict_batch():
    r = client.post("/api/v1/predict/batch", json=[VALID_ORDER, LOW_RISK_ORDER])
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 2
    assert body["summary"]["total_orders"] == 2


def test_predict_rejects_invalid_category():
    bad = dict(VALID_ORDER)
    bad["category"] = "not_a_real_category"
    r = client.post("/api/v1/predict", json=bad)
    assert r.status_code == 422


def test_predict_rejects_negative_order_value():
    bad = dict(VALID_ORDER)
    bad["order_value"] = -100
    r = client.post("/api/v1/predict", json=bad)
    assert r.status_code == 422
