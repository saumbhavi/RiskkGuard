import uuid
import pandas as pd
from app.ml.model import get_model
from app.ml.features import engineer_features, feature_columns
from app.schemas.order import OrderIn, OrderScoreOut, ReasonCode


def score_orders(orders: list[OrderIn]) -> list[OrderScoreOut]:
    model = get_model()
    raw_dicts = []
    for o in orders:
        d = o.model_dump()
        if not d.get("order_id"):
            d["order_id"] = f"TMP-{uuid.uuid4().hex[:8]}"
        raw_dicts.append(d)

    df = pd.DataFrame(raw_dicts)
    engineered = engineer_features(df)
    scored = model.score_frame(df)

    results = []
    for i, row in scored.iterrows():
        reasons = model.reason_codes(raw_dicts[i], engineered.iloc[i])
        results.append(
            OrderScoreOut(
                order_id=row["order_id"],
                risk_score=round(float(row["risk_score"]), 4),
                risk_tier=row["risk_tier"],
                reason_codes=[ReasonCode(**r) for r in reasons],
            )
        )
    return results


def summarize(results: list[OrderScoreOut]) -> dict:
    total = len(results)
    if total == 0:
        return {"total_orders": 0}
    tiers = {"low": 0, "medium": 0, "high": 0}
    for r in results:
        tiers[r.risk_tier] += 1
    avg_score = sum(r.risk_score for r in results) / total
    return {
        "total_orders": total,
        "low_risk": tiers["low"],
        "medium_risk": tiers["medium"],
        "high_risk": tiers["high"],
        "high_risk_pct": round(tiers["high"] / total * 100, 1),
        "avg_risk_score": round(avg_score, 4),
    }
