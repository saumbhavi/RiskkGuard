"""
Synthetic order data generator.

IMPORTANT — read this before trusting the metrics blindly:
This project ships with a SYNTHETIC dataset because no live merchant order
feed is available in this environment. The generator below encodes a
latent "true" return-risk function based on well-documented real-world
return-risk drivers (payment method, discount depth, category return
base-rate, customer return history, seller rating, delivery delay,
price deviation). The model is then trained and evaluated on data it has
never seen, using a TIME-BASED split (not random), so the reported
precision/recall are honest for this synthetic world.

To go to production: replace `generate_dataset()` with a query against
the merchant's real order + returns tables (see docs/DEPLOYMENT.md,
"Swapping in real data"). Nothing else in the pipeline needs to change —
`features.py` operates on the same column schema either way.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

CATEGORIES = ["fashion", "electronics", "home", "beauty", "grocery", "other"]
# Real-world-informed base return rates by category (fashion/electronics run
# highest due to sizing/spec mismatch; grocery lowest).
CATEGORY_BASE_RETURN_RATE = {
    "fashion": 0.22,
    "electronics": 0.14,
    "home": 0.09,
    "beauty": 0.07,
    "grocery": 0.02,
    "other": 0.08,
}
PAYMENT_METHODS = ["cod", "prepaid_card", "upi", "wallet"]
# COD orders are well documented (industry + academic literature) to have
# materially higher return/RTO rates than prepaid.
PAYMENT_RISK_WEIGHT = {"cod": 1.0, "prepaid_card": 0.25, "upi": 0.35, "wallet": 0.4}


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def generate_dataset(n_rows: int = 40000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    start_date = datetime(2025, 1, 1)
    order_offsets = rng.integers(0, 365 * 1.5, size=n_rows)  # 1.5 years of orders
    order_date = [start_date + timedelta(days=int(d)) for d in order_offsets]

    category = rng.choice(CATEGORIES, size=n_rows, p=[0.22, 0.20, 0.18, 0.15, 0.15, 0.10])
    payment_method = rng.choice(PAYMENT_METHODS, size=n_rows, p=[0.38, 0.30, 0.24, 0.08])

    order_value = np.round(np.exp(rng.normal(6.8, 0.9, size=n_rows)), 2)  # ~ INR 300 - 15000, right-skewed
    discount_pct = np.clip(rng.beta(1.5, 6, size=n_rows) * 100, 0, 90).round(1)

    customer_tenure_days = rng.integers(0, 1500, size=n_rows)
    customer_past_orders = np.clip(rng.poisson(customer_tenure_days / 120 + 0.5), 0, 200)
    # Latent per-customer "return propensity" -> generates past_returns correlated with future return
    customer_propensity = rng.beta(1.3, 9, size=n_rows)  # most customers low propensity, long tail
    customer_past_returns = np.array(
        [rng.binomial(n, p) for n, p in zip(customer_past_orders, customer_propensity)]
    )
    customer_return_rate = (customer_past_returns + 1) / (customer_past_orders + 4)  # smoothed (Bayesian prior)

    seller_rating = np.clip(rng.normal(4.2, 0.5, size=n_rows), 1.0, 5.0).round(2)
    delivery_days = np.clip(rng.gamma(3, 1.3, size=n_rows), 1, 21).round(0)
    promised_delivery_days = np.clip(rng.gamma(3, 1.0, size=n_rows), 1, 14).round(0)
    delivery_delay_days = np.clip(delivery_days - promised_delivery_days, 0, None)

    category_avg_price = pd.Series(category).map(
        {"fashion": 1400, "electronics": 6500, "home": 2200, "beauty": 900, "grocery": 500, "other": 1200}
    ).values
    price_deviation_pct = ((order_value - category_avg_price) / category_avg_price * 100).round(1)

    is_weekend = rng.integers(0, 2, size=n_rows)
    hour_of_day = rng.integers(0, 24, size=n_rows)
    distance_km = np.clip(rng.gamma(2, 60, size=n_rows), 2, 2500).round(1)

    # ---- Latent true risk (logit). This is the "ground truth" generative
    # process — a real deployment would not have this, it would only have
    # observed labels. We keep it explicit and inspectable here for audit.
    category_risk = pd.Series(category).map(CATEGORY_BASE_RETURN_RATE).values
    payment_risk = pd.Series(payment_method).map(PAYMENT_RISK_WEIGHT).values

    logit = (
        -3.95
        + 2.6 * category_risk
        + 1.3 * payment_risk
        + 0.018 * discount_pct
        + 3.0 * customer_return_rate
        + 0.10 * delivery_delay_days
        - 0.35 * (seller_rating - 4.2)
        + 0.006 * np.abs(price_deviation_pct)
        - 0.0006 * customer_tenure_days
        + 0.10 * is_weekend
        + 0.0009 * distance_km
    )
    noise = rng.normal(0, 0.55, size=n_rows)  # irreducible noise — no model gets this to AUC=1.0
    true_prob = _sigmoid(logit + noise)
    returned = rng.binomial(1, true_prob)

    df = pd.DataFrame(
        {
            "order_id": [f"ORD{100000+i}" for i in range(n_rows)],
            "order_date": order_date,
            "category": category,
            "payment_method": payment_method,
            "order_value": order_value,
            "discount_pct": discount_pct,
            "customer_tenure_days": customer_tenure_days,
            "customer_past_orders": customer_past_orders,
            "customer_past_returns": customer_past_returns,
            "seller_rating": seller_rating,
            "delivery_days": delivery_days,
            "promised_delivery_days": promised_delivery_days,
            "price_deviation_pct": price_deviation_pct,
            "is_weekend_purchase": is_weekend,
            "hour_of_day": hour_of_day,
            "distance_km": distance_km,
            "returned": returned,
        }
    )
    return df.sort_values("order_date").reset_index(drop=True)


if __name__ == "__main__":
    df = generate_dataset()
    print(df.shape)
    print(df["returned"].mean())
    print(df.head())
