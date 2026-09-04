import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.schemas.order import OrderIn, OrderScoreOut, BatchScoreOut
from app.services.risk_service import score_orders, summarize
from app.ml.model import get_model

router = APIRouter(prefix=settings.api_v1_prefix)


@router.get("/health")
def health():
    try:
        model = get_model()
        return {"status": "ok", "model_trained_at": model.metrics["trained_at"], "operating_threshold": model.threshold}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/metrics")
def get_metrics():
    """Full held-out evaluation report: PR curve, cost curve, confusion
    matrix, feature importance. This is what backs the Model Metrics
    dashboard page — nothing on that page is invented client-side."""
    model = get_model()
    return model.metrics


@router.post("/predict", response_model=OrderScoreOut)
def predict_single(order: OrderIn):
    results = score_orders([order])
    return results[0]


@router.post("/predict/batch", response_model=BatchScoreOut)
def predict_batch(orders: list[OrderIn]):
    if len(orders) > settings.max_batch_size:
        raise HTTPException(status_code=413, detail=f"Batch too large; max {settings.max_batch_size} orders per request.")
    results = score_orders(orders)
    return BatchScoreOut(results=results, summary=summarize(results))


@router.post("/predict/csv", response_model=BatchScoreOut)
async def predict_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")
    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    if len(df) > settings.max_batch_size:
        raise HTTPException(status_code=413, detail=f"CSV too large; max {settings.max_batch_size} rows.")

    required_cols = {"category", "payment_method", "order_value"}
    missing = required_cols - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV missing required columns: {sorted(missing)}")

    df = df.where(pd.notnull(df), None)
    try:
        orders = [OrderIn(**row) for row in df.to_dict(orient="records")]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Row validation failed: {e}")

    results = score_orders(orders)
    return BatchScoreOut(results=results, summary=summarize(results))
