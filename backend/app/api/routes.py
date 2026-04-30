from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import FRONTEND_ORIGIN
from app.services.fastf1_service import get_schedule
from app.services.prediction_service import backtest_model, predict_event, predict_next_race


app = FastAPI(title="F1 Winner Prediction API", version="1.0.0")

app.add_middleware(
  CORSMiddleware,
  allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:3000"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
  return {"status": "ok"}


@app.get("/api/seasons")
def seasons() -> list[dict]:
  return [
    {"year": year, "rounds": int(len(get_schedule(year)[get_schedule(year)["RoundNumber"].fillna(0) > 0]))}
    for year in range(2022, 2027)
  ]


@app.get("/api/predictions/next-race")
async def next_race_prediction() -> dict:
  return await predict_next_race()


@app.get("/api/predictions/{year}/{round_number}")
async def event_prediction(year: int, round_number: int) -> dict:
  return await predict_event(year, round_number)


@app.get("/api/evaluation/backtest")
def evaluation_backtest(
  train_start_year: int = 2018,
  test_year: int = 2019,
) -> dict:
  return backtest_model(train_start_year=train_start_year, test_year=test_year)
