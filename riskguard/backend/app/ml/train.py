"""
Trains the return-risk model and writes all serving artifacts to
app/ml/artifacts/. Run with: python -m app.ml.train

Design choices (documented, not buried):
  - Model: HistGradientBoostingClassifier (scikit-learn). Chosen over
    XGBoost/LightGBM to keep the deploy footprint to pure scikit-learn —
    one fewer compiled dependency, faster Docker builds, same accuracy
    class for tabular data at this scale.
  - Split: TIME-BASED (train on the earlier 80% of orders by date, test
    on the most recent 20%). A random split would leak future customer
    return-history into the past and overstate accuracy. This is the
    single most common mistake in return-risk model evaluations.
  - Threshold: NOT fixed at 0.5. We sweep thresholds and pick the one
    that maximizes net financial value using explicit, editable cost
    assumptions (see COST_ASSUMPTIONS below), because a merchant does not
    care about F1 — they care about rupees.
"""
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    precision_recall_curve,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
)

from app.ml.data_gen import generate_dataset
from app.ml.features import engineer_features, feature_columns

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
ARTIFACT_DIR.mkdir(exist_ok=True)

# --- Editable business cost assumptions (INR). A merchant plugs their own
# numbers in here at deploy time — see docs/DEPLOYMENT.md.
COST_ASSUMPTIONS = {
    # Avg fully-loaded cost of a return we correctly catch and intervene on
    # (reverse logistics + restocking + payment reversal + support time),
    # discounted by an assumed intervention success rate.
    "avg_return_cost_saved_per_tp": 260.0,
    # Avg margin/goodwill cost of adding friction (extra verification step,
    # COD-to-prepaid nudge, manual review) to a customer who was NOT going
    # to return the order — the false-positive cost the brief asks for.
    "avg_friction_cost_per_fp": 45.0,
}


def time_based_split(df: pd.DataFrame, test_frac: float = 0.2):
    df = df.sort_values("order_date").reset_index(drop=True)
    split_idx = int(len(df) * (1 - test_frac))
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()


def compute_cost_curve(y_true, y_scores, thresholds, assumptions):
    rows = []
    for t in thresholds:
        preds = (y_scores >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, preds, labels=[0, 1]).ravel()
        net_value = tp * assumptions["avg_return_cost_saved_per_tp"] - fp * assumptions["avg_friction_cost_per_fp"]
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        rows.append(
            {
                "threshold": round(float(t), 3),
                "tp": int(tp),
                "fp": int(fp),
                "fn": int(fn),
                "tn": int(tn),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "net_value_inr": round(float(net_value), 2),
            }
        )
    return rows


def main():
    print("Generating synthetic dataset...")
    df = generate_dataset(n_rows=40000, seed=42)

    train_df, test_df = time_based_split(df, test_frac=0.2)
    print(f"Train: {len(train_df)} orders ({train_df['order_date'].min().date()} to {train_df['order_date'].max().date()})")
    print(f"Test:  {len(test_df)} orders ({test_df['order_date'].min().date()} to {test_df['order_date'].max().date()})")

    X_train = engineer_features(train_df)[feature_columns()]
    y_train = train_df["returned"].values
    X_test = engineer_features(test_df)[feature_columns()]
    y_test = test_df["returned"].values

    print("Training HistGradientBoostingClassifier...")
    model = HistGradientBoostingClassifier(
        max_iter=250,
        max_depth=6,
        learning_rate=0.06,
        l2_regularization=0.5,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.15,
    )
    model.fit(X_train, y_train)

    scores = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, scores)
    ap = average_precision_score(y_test, scores)
    print(f"Held-out ROC-AUC: {auc:.4f} | Average Precision: {ap:.4f}")

    prec, rec, pr_thresholds = precision_recall_curve(y_test, scores)
    pr_curve = [
        {"threshold": round(float(t), 3), "precision": round(float(p), 4), "recall": round(float(r), 4)}
        for p, r, t in zip(prec[:-1], rec[:-1], pr_thresholds)
    ]
    # Downsample PR curve for a lighter payload to the frontend
    pr_curve_sampled = pr_curve[:: max(1, len(pr_curve) // 60)]

    sweep_thresholds = np.round(np.arange(0.05, 0.96, 0.05), 2)
    cost_curve = compute_cost_curve(y_test, scores, sweep_thresholds, COST_ASSUMPTIONS)
    best = max(cost_curve, key=lambda r: r["net_value_inr"])
    best_threshold = best["threshold"]
    print(f"Cost-optimal threshold: {best_threshold} -> net value INR {best['net_value_inr']} on {len(test_df)} held-out orders")

    final_preds = (scores >= best_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, final_preds, labels=[0, 1]).ravel()
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    importances = model.feature_importances_ if hasattr(model, "feature_importances_") else None
    if importances is None:
        # HistGradientBoostingClassifier has no native feature_importances_;
        # use permutation importance on a subsample for speed.
        from sklearn.inspection import permutation_importance

        sub_idx = np.random.default_rng(0).choice(len(X_test), size=min(4000, len(X_test)), replace=False)
        perm = permutation_importance(
            model, X_test.iloc[sub_idx], y_test[sub_idx], n_repeats=5, random_state=0, scoring="average_precision"
        )
        importances = perm.importances_mean
        importances = np.clip(importances, 0, None)

    feat_imp = sorted(
        zip(feature_columns(), importances.tolist()), key=lambda kv: kv[1], reverse=True
    )
    feat_imp = [{"feature": f, "importance": round(v, 5)} for f, v in feat_imp]
    total_imp = sum(f["importance"] for f in feat_imp) or 1.0
    for f in feat_imp:
        f["importance_pct"] = round(f["importance"] / total_imp * 100, 2)

    metrics = {
        "trained_at": pd.Timestamp.utcnow().isoformat(),
        "dataset": {
            "source": "synthetic (see app/ml/data_gen.py) — replace with real order history before production use",
            "n_total": int(len(df)),
            "n_train": int(len(train_df)),
            "n_test": int(len(test_df)),
            "base_return_rate": round(float(df["returned"].mean()), 4),
            "split_method": "time_based_80_20",
            "train_date_range": [str(train_df["order_date"].min().date()), str(train_df["order_date"].max().date())],
            "test_date_range": [str(test_df["order_date"].min().date()), str(test_df["order_date"].max().date())],
        },
        "headline": {
            "roc_auc": round(float(auc), 4),
            "average_precision": round(float(ap), 4),
            "operating_threshold": best_threshold,
            "precision_at_threshold": round(precision, 4),
            "recall_at_threshold": round(recall, 4),
            "f1_at_threshold": round(f1, 4),
            "confusion_matrix": {"tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn)},
            "estimated_net_value_inr_on_test_set": best["net_value_inr"],
            "n_test_orders": int(len(test_df)),
        },
        "cost_assumptions": COST_ASSUMPTIONS,
        "cost_curve": cost_curve,
        "pr_curve": pr_curve_sampled,
        "feature_importance": feat_imp,
    }

    joblib.dump(model, ARTIFACT_DIR / "model.pkl")
    with open(ARTIFACT_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    with open(ARTIFACT_DIR / "feature_columns.json", "w") as f:
        json.dump(feature_columns(), f, indent=2)

    print(f"Artifacts written to {ARTIFACT_DIR}")
    print(f"Precision @ operating threshold: {precision:.3f} | Recall: {recall:.3f} | F1: {f1:.3f}")


if __name__ == "__main__":
    main()
