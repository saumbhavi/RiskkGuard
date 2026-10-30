# RiskGuard — Return-Risk Console

Scores incoming e-commerce orders for return risk at checkout/fulfillment time,
so a merchant can route only the genuinely risky orders to manual review,
COD-to-prepaid nudges, or extra verification — instead of adding friction to
every order.

**Scope, deliberately:** this is a defense-only decision-support tool. It
scores and explains; it never blocks, cancels, or auto-actions an order. Every
flag is a recommendation a human (or the merchant's existing OMS rules) acts
on.

## Why this shape-

A merchant doesn't care about F1 score — they care about rupees saved vs.
rupees lost to friction. The whole system is built around that:

- The serving threshold isn't 0.5 by default — it's chosen by sweeping
  thresholds against explicit, editable cost assumptions (`avg return cost
  saved` vs. `avg friction cost`) and picking the one that maximizes net
  value. See `backend/app/ml/train.py::COST_ASSUMPTIONS`.
- Evaluation uses a **time-based** train/test split (train on older orders,
  test on the most recent slice), not a random split — a random split would
  leak future customer history into the past and overstate accuracy.
- Every score ships with **reason codes** (adverse-action-code style, the
  same pattern credit risk systems use), not just a bare probability, so a
  reviewer or the merchant's ops team can see *why*.
- Metrics on the dashboard are pulled live from `/api/v1/metrics` — nothing
  is hardcoded in the frontend. What you see is what the held-out test set
  actually produced.

## Current honest numbers (synthetic dataset — see below)

On a 8,000-order held-out set, time-split from a 40,000-order synthetic
dataset: **ROC-AUC 0.72**, precision **0.30** / recall **0.77** at the
cost-optimal threshold (0.15). That precision looks low next to a marketing
slide — it's the honest number for a base rate of ~21% at a threshold chosen
to catch three-quarters of returns. The cost curve in the Model Performance
tab shows exactly how precision and net value trade off across thresholds,
so a merchant can pick a stricter threshold if false positives are more
expensive for them.

**⚠️ Dataset disclosure:** no live merchant order feed was available to
build this, so `backend/app/ml/data_gen.py` generates a synthetic dataset
from a documented, inspectable latent risk function (payment method,
discount depth, category base return rate, customer return history, seller
rating, delivery delay, price deviation — all real, published return-risk
drivers). The model and evaluation pipeline are production-shaped; the
*data* is a stand-in. See "Swapping in real data" in
`docs/DEPLOYMENT.md` — nothing else in the pipeline changes.

## Architecture

```
riskguard/
├── backend/                 FastAPI + scikit-learn service
│   ├── app/
│   │   ├── main.py          App entrypoint, CORS, startup checks
│   │   ├── api/routes.py    /predict, /predict/batch, /predict/csv, /metrics, /health
│   │   ├── schemas/         Pydantic request/response contracts
│   │   ├── services/        Business logic between API and ML layer
│   │   └── ml/
│   │       ├── data_gen.py  Synthetic dataset (documented latent risk fn)
│   │       ├── features.py  SHARED feature engineering (train + serve — no skew)
│   │       ├── train.py     Time-split training, cost-curve threshold selection
│   │       ├── model.py     Inference wrapper + reason-code generation
│   │       └── artifacts/   model.pkl, metrics.json (generated, not hand-written)
│   ├── tests/test_api.py    7 tests: health, metrics shape, ranking sanity, validation
│   └── Dockerfile           Trains the model at image build time
├── frontend/                 React + Vite + Tailwind (light theme)
│   ├── src/pages/Dashboard.jsx      Single-order form + CSV batch upload
│   ├── src/pages/ModelMetrics.jsx   Live PR curve, cost curve, confusion matrix
│   └── Dockerfile + nginx.conf      Serves static build, proxies /api to backend
├── docker-compose.yml        One command, two services
└── docs/DEPLOYMENT.md
```

One feature-engineering module (`features.py`) is imported by both training
and inference — the single most common source of silent accuracy loss in
risk models is computing a feature slightly differently at serve time than
at train time, so that logic lives in exactly one place.

## Quickstart

```bash
docker compose up --build
```

- Frontend: http://localhost:8080
- Backend API docs: http://localhost:8000/docs

Full deployment options (including without Docker, and swapping in real
merchant data) are in `docs/DEPLOYMENT.md`.

## Running tests

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.ml.train      # generates model artifacts, prints held-out metrics
python -m pytest tests/ -v  # 7 tests
```

## What's out of scope (by design)

- No automated order blocking/cancellation — this is a scoring and
  explanation layer only.
- No PII storage — the API is stateless; nothing is persisted server-side
  between requests. A real deployment would add an orders/audit-log
  database, which is a straightforward addition (see DEPLOYMENT.md) but was
  left out to keep the reviewable surface area honest about what's actually
  built vs. described.
