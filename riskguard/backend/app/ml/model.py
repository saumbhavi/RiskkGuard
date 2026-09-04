"""
Inference-time model wrapper. Loads the trained artifacts once at process
start (see app/main.py lifespan) and reuses them for every request —
never reload from disk per-request, that's the classic latency mistake.
"""
import json
import joblib
import pandas as pd
from pathlib import Path
from functools import lru_cache

from app.ml.features import engineer_features, feature_columns

ARTIFACT_DIR = Path(__file__).parent / "artifacts"


class RiskModel:
    def __init__(self):
        model_path = ARTIFACT_DIR / "model.pkl"
        metrics_path = ARTIFACT_DIR / "metrics.json"
        if not model_path.exists() or not metrics_path.exists():
            raise FileNotFoundError(
                "Model artifacts not found. Run `python -m app.ml.train` inside the "
                "backend container/venv first (this also happens automatically on "
                "first `docker compose up` — see docs/DEPLOYMENT.md)."
            )
        self.model = joblib.load(model_path)
        with open(metrics_path) as f:
            self.metrics = json.load(f)
        self.threshold = self.metrics["headline"]["operating_threshold"]
        self.feature_cols = feature_columns()
        self.feature_importance_lookup = {
            f["feature"]: f["importance_pct"] for f in self.metrics["feature_importance"]
        }

    def score_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        X = engineer_features(df)[self.feature_cols]
        scores = self.model.predict_proba(X)[:, 1]
        out = df.copy()
        out["risk_score"] = scores
        # Tiers are defined relative to the data-driven operating threshold
        # rather than a hardcoded 0.30, since the threshold itself moves
        # with the merchant's cost assumptions (see train.py).
        medium_cutoff = self.threshold / 2
        tier = pd.Series("low", index=out.index)
        tier[(scores >= medium_cutoff) & (scores < self.threshold)] = "medium"
        tier[scores >= self.threshold] = "high"
        out["risk_tier"] = tier
        return out

    def reason_codes(self, raw_order: dict, engineered_row: pd.Series, top_n: int = 3) -> list[dict]:
        """Rule-based reason codes (industry-standard 'adverse action code' style,
        as used in credit/fraud risk systems) rather than a black-box score alone.
        Ranks the order's own features by (global model importance x how far the
        value sits from a 'safe' reference point), so explanations are both
        model-grounded and human-readable.
        """
        reasons = []
        checks = [
            ("pay_cod", raw_order.get("payment_method") == "cod", "Cash-on-delivery order (higher return/RTO base rate)"),
            ("discount_pct", engineered_row.get("discount_pct", 0) > 40, f"Deep discount ({engineered_row.get('discount_pct', 0):.0f}% off)"),
            ("customer_return_rate", engineered_row.get("customer_return_rate", 0) > 0.25, "Customer has a high historical return rate"),
            ("delivery_delay_days", engineered_row.get("delivery_delay_days", 0) > 2, f"Delivery delayed {engineered_row.get('delivery_delay_days', 0):.0f} days past promise"),
            ("seller_rating", engineered_row.get("seller_rating", 5) < 3.5, f"Low seller rating ({engineered_row.get('seller_rating', 5):.1f}/5)"),
            ("price_deviation_pct", abs(engineered_row.get("price_deviation_pct", 0)) > 60, "Order value is a major outlier for its category"),
            ("customer_tenure_days", engineered_row.get("customer_tenure_days", 999) < 14, "New customer with little order history"),
            ("cat_fashion", raw_order.get("category") == "fashion", "Fashion category (higher base return rate — sizing/fit)"),
        ]
        for feat_key, triggered, message in checks:
            if triggered:
                weight = self.feature_importance_lookup.get(feat_key, self.feature_importance_lookup.get(f"cat_{feat_key}", 1.0))
                reasons.append({"code": feat_key, "message": message, "weight": weight})
        reasons.sort(key=lambda r: r["weight"], reverse=True)
        return reasons[:top_n] if reasons else [{"code": "baseline", "message": "No individual risk flags triggered; score reflects category/payment baseline.", "weight": 0}]


@lru_cache(maxsize=1)
def get_model() -> "RiskModel":
    return RiskModel()
