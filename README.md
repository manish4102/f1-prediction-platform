---
title: F1 Cortex Predictor API
emoji: "🏎️"
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
suggested_hardware: cpu-basic
---

# F1 Winner Prediction Platform

This project predicts the most likely winner of the next Formula 1 race using:

- FastF1 race and qualifying data
- a weather API for race-weekend conditions
- a scikit-learn random forest model selected through historical backtesting
- a FastAPI backend
- a Next.js frontend

## What It Predicts

- projected winner
- top contenders
- nearest challengers
- confidence score
- feature-driven explanation

## Model Strategy

The platform trains a per-driver pre-race scoring model on historical events and
predicts a normalized performance score for the upcoming event.

Key features:

- recent finishing form
- recent qualifying form
- podium rate
- DNF rate
- teammate-relative strength
- prior result at the same circuit
- wet-race adaptability signal
- weather-adjusted risk modifier

The winner prediction is the top-ranked driver by forecast score. Probabilities
are calibrated from the ranked scores into a relative likelihood distribution.

## Project Structure

```text
f1/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── .env.example
└── shared/
    └── contracts.ts
```

## Backend Setup

```bash
cd /Users/manishparmar/Desktop/Everything/Projects/f1/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Frontend Setup

```bash
cd /Users/manishparmar/Desktop/Everything/Projects/f1/frontend
cp .env.example .env.local
npm install
npm run dev
```

## Environment Variables

Backend:

```bash
FASTF1_CACHE_DIR=/Users/manishparmar/Desktop/Everything/Projects/f1/backend/cache
OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast
```

Frontend:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Vercel

This repo includes a root [vercel.json](/Users/manishparmar/Desktop/Everything/Projects/f1/vercel.json)
configured for Vercel multi-service deployments:

- `frontend` -> `frontend/`
- `backend` -> `backend/`
- backend route prefix -> `/_/backend`

On Vercel, the frontend automatically defaults to:

```text
https://<your-deployment-host>/_/backend
```

for API calls when `NEXT_PUBLIC_API_BASE_URL` is not explicitly set.

Deploy flow:

1. Import the GitHub repo into Vercel.
2. Keep the project root at the repository root.
3. Let Vercel detect the root `vercel.json` multi-service config.
4. If you want to override the backend URL manually, set `NEXT_PUBLIC_API_BASE_URL`.
5. Redeploy after any backend or frontend changes.

## Hugging Face Spaces

This repo also includes a root [Dockerfile](/Users/manishparmar/Desktop/Everything/Projects/f1/Dockerfile) so the FastAPI backend can be deployed as a Docker Space on Hugging Face.

Recommended setup:

1. Keep the Next.js frontend on Vercel.
2. Create a new Hugging Face Space using `Docker`.
3. Point that Space at this repository or push this repository into the Space repo.
4. In the Space settings, set `FRONTEND_ORIGIN=https://<your-vercel-frontend-domain>`.
5. In Vercel, set `NEXT_PUBLIC_API_BASE_URL=https://<your-space-subdomain>.hf.space`.
6. Redeploy the frontend after updating the Vercel environment variable.

Notes:

- The Docker Space serves the FastAPI API on port `7860`.
- FastF1 cache defaults to `/tmp/fastf1-cache` inside the container.
- The next-race prediction response is cached in memory for 30 minutes to reduce repeated FastF1 load times.
- The first cold request can still take noticeably longer than warmed requests.

## Main Endpoints

- `GET /api/health`
- `GET /api/seasons`
- `GET /api/predictions/next-race`
- `GET /api/predictions/{year}/{round}`
- `GET /api/evaluation/backtest?train_start_year=2018&test_year=2019`

## Notes

- The prediction is pre-race and does not rely on future qualifying or future
  race outcomes.
- If live weather is unavailable, the model falls back to historical weather
  averages and still returns a prediction.
- The app is designed to return the winner plus the closest alternatives, not
  just a single name.
- The historical evaluation route performs a walk-forward backtest over the
  selected test year, training each race prediction only on races that
  happened before it.
- The current best historical baseline was selected on a 2019 walk-forward
  backtest and uses a random forest model.
