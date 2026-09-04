# Deployment

## Option A — Docker Compose (recommended, one command)

Requires Docker + Docker Compose.

```bash
git clone <your-repo-url>
cd riskguard
docker compose up --build
```

This builds two images:
- `backend` — trains the model during the image build (`RUN python -m
  app.ml.train` in `backend/Dockerfile`), then serves the API on `:8000`.
- `frontend` — builds the React app, serves it via nginx on `:8080`, and
  reverse-proxies `/api/*` to the backend container so the browser only
  ever talks to one origin (no CORS headaches, no hardcoded backend URL).

Open http://localhost:8080. Tear down with `docker compose down`.

To retrain (e.g. after editing `COST_ASSUMPTIONS` or the feature set):
```bash
docker compose build backend --no-cache
docker compose up -d backend
```

## Option B — Without Docker (local dev)

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.ml.train           # writes app/ml/artifacts/{model.pkl,metrics.json}
uvicorn app.main:app --reload --port 8000
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173, proxies /api to :8000 via vite.config.js
```

## Option C — Cloud deploy (single VPS)

Any VM with Docker installed (a ₹500–1000/mo VPS is plenty for this
workload — it's a single gradient-boosted tree model, not a deep net):

1. `git clone` the repo onto the VM.
2. `docker compose up -d --build`.
3. Put a reverse proxy (Caddy or nginx) in front of port 8080 for TLS, or
   point a managed load balancer at it.
4. For a subdomain-per-service split instead (e.g. `api.yourdomain.com` +
   `app.yourdomain.com`), deploy `backend/` and `frontend/` as two separate
   services on Render / Railway / Fly.io — both are plain Dockerfiles, no
   platform-specific config needed. Set `RISKGUARD_CORS_ORIGINS` on the
   backend to the frontend's real origin, and `VITE_API_BASE_URL` as a
   frontend build-time env var pointing at the backend's real URL.

## Swapping in real merchant data

Everything downstream of the dataset is already production-shaped. To go
live with real data, replace one function:

1. Open `backend/app/ml/data_gen.py`.
2. Replace the body of `generate_dataset()` with a query against your real
   order + returns tables. It must return a DataFrame with these columns
   (see the function's current synthetic output for exact dtypes):
   `order_date, category, payment_method, order_value, discount_pct,
   customer_tenure_days, customer_past_orders, customer_past_returns,
   seller_rating, delivery_days, promised_delivery_days,
   price_deviation_pct, is_weekend_purchase, hour_of_day, distance_km,
   returned`.
3. Update `COST_ASSUMPTIONS` in `train.py` with your actual average return
   cost and friction cost per order.
4. Re-run `python -m app.ml.train` (or rebuild the backend Docker image —
   training happens automatically on build).

Nothing in `features.py`, `model.py`, the API routes, or the frontend needs
to change — they all operate on the same column schema regardless of where
the rows came from.

## Extending

- **New features:** add the raw column in `data_gen.py`, add it to
  `NUMERIC_FEATURES`/`CATEGORICAL_FEATURES` in `features.py`, retrain.
- **Persisting scored orders / audit trail:** add a `db/` module
  (SQLAlchemy + SQLite or Postgres) and write each `OrderScoreOut` to it
  inside `risk_service.score_orders()`. Left out of this build to keep the
  surface area matched to what's actually tested.
- **Auth:** put the backend behind an API key or JWT check in
  `app/api/routes.py` (FastAPI `Depends`) before exposing it beyond a
  trusted internal network.
