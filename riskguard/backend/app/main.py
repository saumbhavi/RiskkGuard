import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import router
from app.ml.model import get_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("riskguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        model = get_model()
        logger.info(f"Model loaded. Trained at {model.metrics['trained_at']}, operating threshold {model.threshold}")
    except FileNotFoundError as e:
        logger.warning(f"Model artifacts missing at startup: {e}. /api/v1/health will report 503 until trained.")
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Return-risk scoring API for e-commerce merchants. Defense-only: scores and explains risk, takes no automated punitive action.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"service": settings.app_name, "docs": "/docs", "api": settings.api_v1_prefix}
