"""
Single source of truth for feature engineering.

CRITICAL: this module is imported by BOTH train.py and model.py (inference).
This is deliberate — the #1 cause of silent accuracy loss in production risk
models is train/serve skew (features computed slightly differently at
inference than at training time). Never duplicate this logic elsewhere.
"""
from __future__ import annotations
import pandas as pd

NUMERIC_FEATURES = [
    "order_value",
    "discount_pct",
    "customer_tenure_days",
    "customer_past_orders",
    "customer_return_rate",
    "seller_rating",
    "delivery_delay_days",
    "price_deviation_pct",
    "is_weekend_purchase",
    "hour_of_day",
    "distance_km",
]
CATEGORICAL_FEATURES = ["category", "payment_method"]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Fixed category ordering -> stable one-hot columns across train/serve.
CATEGORIES = ["fashion", "electronics", "home", "beauty", "grocery", "other"]
PAYMENT_METHODS = ["cod", "prepaid_card", "upi", "wallet"]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive model-ready features from raw order fields.

    Accepts either the synthetic training frame (has customer_past_returns)
    or a single incoming order dict-turned-frame from the API. Missing
    optional columns are defaulted sensibly rather than raising, since
    at inference time a brand-new customer legitimately has no history.
    """
    out = df.copy()

    if "customer_past_returns" not in out.columns:
        out["customer_past_returns"] = 0
    if "customer_past_orders" not in out.columns:
        out["customer_past_orders"] = 0
    if "promised_delivery_days" not in out.columns:
        out["promised_delivery_days"] = out.get("delivery_days", 3)
    if "delivery_days" not in out.columns:
        out["delivery_days"] = out["promised_delivery_days"]

    # Bayesian-smoothed return rate: (past_returns + 1) / (past_orders + 4)
    # avoids a brand-new customer being scored as 0% or 100% risk off one data point.
    out["customer_return_rate"] = (out["customer_past_returns"] + 1) / (out["customer_past_orders"] + 4)

    out["delivery_delay_days"] = (out["delivery_days"] - out["promised_delivery_days"]).clip(lower=0)

    if "price_deviation_pct" not in out.columns:
        cat_avg = out["category"].map(
            {"fashion": 1400, "electronics": 6500, "home": 2200, "beauty": 900, "grocery": 500, "other": 1200}
        ).fillna(1200)
        out["price_deviation_pct"] = ((out["order_value"] - cat_avg) / cat_avg * 100).round(1)

    for col in NUMERIC_FEATURES:
        if col not in out.columns:
            out[col] = 0

    out["category"] = out["category"].where(out["category"].isin(CATEGORIES), "other")
    out["payment_method"] = out["payment_method"].where(out["payment_method"].isin(PAYMENT_METHODS), "upi")

    cat_dummies = pd.get_dummies(out["category"], prefix="cat")
    for c in CATEGORIES:
        col = f"cat_{c}"
        if col not in cat_dummies.columns:
            cat_dummies[col] = 0
    cat_dummies = cat_dummies[[f"cat_{c}" for c in CATEGORIES]]

    pay_dummies = pd.get_dummies(out["payment_method"], prefix="pay")
    for p in PAYMENT_METHODS:
        col = f"pay_{p}"
        if col not in pay_dummies.columns:
            pay_dummies[col] = 0
    pay_dummies = pay_dummies[[f"pay_{p}" for p in PAYMENT_METHODS]]

    X = pd.concat([out[NUMERIC_FEATURES].reset_index(drop=True), cat_dummies.reset_index(drop=True), pay_dummies.reset_index(drop=True)], axis=1)
    return X


def feature_columns() -> list[str]:
    return NUMERIC_FEATURES + [f"cat_{c}" for c in CATEGORIES] + [f"pay_{p}" for p in PAYMENT_METHODS]
