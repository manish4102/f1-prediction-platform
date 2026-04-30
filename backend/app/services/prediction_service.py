from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.services.fastf1_service import (
  future_or_next_event,
  get_schedule,
  historical_events,
  load_race_session,
  recent_completed_events,
)
from app.services.weather_service import get_race_weather


FEATURE_COLUMNS = [
  "recent_finish_avg",
  "recent_finish_std",
  "recent_points_avg",
  "recent_points_trend",
  "podium_rate",
  "win_rate",
  "dnf_rate",
  "same_track_finish_avg",
  "teammate_delta_avg",
  "wet_skill",
  "season_points_to_date",
]

DEFAULT_FEATURES = {
  "recent_finish_avg": 12.0,
  "recent_finish_std": 4.0,
  "recent_points_avg": 0.0,
  "recent_points_trend": 0.0,
  "podium_rate": 0.0,
  "win_rate": 0.0,
  "dnf_rate": 0.0,
  "same_track_finish_avg": 10.0,
  "teammate_delta_avg": 0.0,
  "wet_skill": 0.0,
  "season_points_to_date": 0.0,
}

FINISH_POINTS = {
  1: 25.0,
  2: 18.0,
  3: 15.0,
  4: 12.0,
  5: 10.0,
  6: 8.0,
  7: 6.0,
  8: 4.0,
  9: 2.0,
  10: 1.0,
}


def _candidate_models() -> dict[str, Any]:
  return {
    "logistic_regression": Pipeline(
      [
        ("scaler", StandardScaler()),
        (
          "model",
          LogisticRegression(
            class_weight="balanced",
            max_iter=4000,
            C=0.7,
            solver="lbfgs",
            random_state=7,
          ),
        ),
      ]
    ),
    "random_forest": RandomForestClassifier(
      n_estimators=450,
      max_depth=9,
      min_samples_leaf=2,
      class_weight="balanced_subsample",
      random_state=7,
      n_jobs=-1,
    ),
    "hist_gradient_boosting": HistGradientBoostingClassifier(
      max_depth=4,
      learning_rate=0.045,
      max_iter=260,
      random_state=7,
    ),
  }


def _safe_rank(value: Any, default: float = 20.0) -> float:
  if value is None or pd.isna(value):
    return default
  return float(value)


def _points_from_finish(position: float | None) -> float:
  pos = int(_safe_rank(position))
  return FINISH_POINTS.get(pos, 0.0)


def _clean_results(session: Any) -> pd.DataFrame:
  results = session.results.copy()
  results["PositionNum"] = pd.to_numeric(results["Position"], errors="coerce")
  results["ClassifiedPositionNum"] = pd.to_numeric(results["ClassifiedPosition"], errors="coerce")
  return results


def _infer_race_finish_positions(session: Any) -> dict[str, float]:
  laps = session.laps[["Driver", "LapNumber", "Position", "Time"]].dropna(subset=["LapNumber"]).copy()
  if laps.empty:
    return {}
  ordered = (
    laps.sort_values(["Driver", "LapNumber", "Time"])
    .groupby("Driver")
    .agg(
      MaxLap=("LapNumber", "max"),
      LastTime=("Time", "max"),
      LastTrackPosition=("Position", "last"),
    )
    .reset_index()
    .sort_values(["MaxLap", "LastTime", "LastTrackPosition"], ascending=[False, True, True])
    .reset_index(drop=True)
  )
  ordered["InferredFinish"] = ordered.index + 1
  return dict(zip(ordered["Driver"], ordered["InferredFinish"]))


@lru_cache(maxsize=128)
def _build_event_frame(year: int, round_number: int) -> pd.DataFrame:
  race = load_race_session(year, round_number)
  race_results = _clean_results(race)
  inferred_finish = _infer_race_finish_positions(race)
  schedule = get_schedule(year)
  schedule_row = schedule[schedule["RoundNumber"] == round_number].iloc[0]
  event_name = str(schedule_row["EventName"])
  country = str(schedule_row.get("Country") or "")
  location = str(schedule_row.get("Location") or "")
  event_date = str(pd.to_datetime(schedule_row["EventDate"]).date())
  wet_race = bool(
    race.weather_data is not None
    and not race.weather_data.empty
    and race.weather_data["Rainfall"].fillna(False).any()
  )

  rows: list[dict[str, Any]] = []
  for _, row in race_results.iterrows():
    driver_code = row["Abbreviation"]
    raw_finish = row.get("PositionNum")
    finish_position = _safe_rank(raw_finish, default=_safe_rank(inferred_finish.get(driver_code)))
    if pd.isna(raw_finish) and driver_code in inferred_finish:
      finish_position = float(inferred_finish[driver_code])
    status = str(row.get("Status", "")).upper()
    rows.append(
      {
        "year": year,
        "round": round_number,
        "eventOrder": year * 100 + round_number,
        "eventName": event_name,
        "eventDate": event_date,
        "country": country,
        "location": location,
        "driverCode": driver_code,
        "fullName": row.get("FullName", driver_code),
        "teamName": row.get("TeamName", ""),
        "finishPosition": finish_position,
        "points": _points_from_finish(finish_position),
        "podium": 1.0 if finish_position <= 3 else 0.0,
        "isWinner": 1 if finish_position == 1 else 0,
        "dnf": 1.0 if status not in {"FINISHED", "+1 LAP", "+2 LAPS", "+3 LAPS"} and finish_position > 10 else 0.0,
        "wetRace": 1.0 if wet_race else 0.0,
      }
    )
  return pd.DataFrame(rows)


def _build_dataset(start_year: int, end_year: int) -> pd.DataFrame:
  frames: list[pd.DataFrame] = []
  for event in historical_events(start_year, end_year):
    try:
      frames.append(_build_event_frame(event["year"], event["round"]))
    except Exception:
      continue
  if not frames:
    raise ValueError("No historical frames could be loaded.")
  dataset = pd.concat(frames, ignore_index=True)
  return _add_features(dataset)


def _add_features(dataset: pd.DataFrame) -> pd.DataFrame:
  dataset = dataset.sort_values(["eventOrder", "driverCode"]).copy()

  dataset["recent_finish_avg"] = (
    dataset.groupby("driverCode")["finishPosition"]
    .transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    .fillna(DEFAULT_FEATURES["recent_finish_avg"])
  )
  dataset["recent_finish_std"] = (
    dataset.groupby("driverCode")["finishPosition"]
    .transform(lambda s: s.shift(1).rolling(5, min_periods=1).std())
    .fillna(DEFAULT_FEATURES["recent_finish_std"])
  )
  dataset["recent_points_avg"] = (
    dataset.groupby("driverCode")["points"]
    .transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    .fillna(DEFAULT_FEATURES["recent_points_avg"])
  )
  dataset["recent_points_trend"] = (
    dataset.groupby("driverCode")["points"]
    .transform(lambda s: s.shift(1).diff().rolling(4, min_periods=1).mean())
    .fillna(DEFAULT_FEATURES["recent_points_trend"])
  )
  dataset["podium_rate"] = (
    dataset.groupby("driverCode")["podium"]
    .transform(lambda s: s.shift(1).rolling(8, min_periods=1).mean())
    .fillna(DEFAULT_FEATURES["podium_rate"])
  )
  dataset["win_rate"] = (
    dataset.groupby("driverCode")["isWinner"]
    .transform(lambda s: s.shift(1).rolling(10, min_periods=1).mean())
    .fillna(DEFAULT_FEATURES["win_rate"])
  )
  dataset["dnf_rate"] = (
    dataset.groupby("driverCode")["dnf"]
    .transform(lambda s: s.shift(1).rolling(8, min_periods=1).mean())
    .fillna(DEFAULT_FEATURES["dnf_rate"])
  )
  dataset["same_track_finish_avg"] = (
    dataset.groupby(["driverCode", "eventName"])["finishPosition"]
    .transform(lambda s: s.shift(1).expanding().mean())
    .fillna(DEFAULT_FEATURES["same_track_finish_avg"])
  )

  teammate_event_mean = dataset.groupby(["eventOrder", "teamName"])["finishPosition"].transform("mean")
  dataset["teammate_delta_raw"] = dataset["finishPosition"] - teammate_event_mean
  dataset["teammate_delta_avg"] = (
    dataset.groupby("driverCode")["teammate_delta_raw"]
    .transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    .fillna(DEFAULT_FEATURES["teammate_delta_avg"])
  )

  dataset["wet_points_source"] = np.where(dataset["wetRace"] == 1.0, dataset["points"], np.nan)
  dataset["wet_skill"] = (
    dataset.groupby("driverCode")["wet_points_source"]
    .transform(lambda s: s.shift(1).rolling(6, min_periods=1).mean())
    .fillna(0.0)
    / 25.0
  )
  dataset["season_points_to_date"] = (
    dataset.groupby(["driverCode", "year"])["points"]
    .transform(lambda s: s.cumsum().shift(1))
    .fillna(DEFAULT_FEATURES["season_points_to_date"])
  )

  for column, default_value in DEFAULT_FEATURES.items():
    dataset[column] = dataset[column].fillna(default_value)
  return dataset


def _predict_probs(model: Any, features: pd.DataFrame) -> np.ndarray:
  raw = model.predict_proba(features)[:, 1]
  total = float(raw.sum())
  if total <= 0:
    return np.repeat(1.0 / len(raw), len(raw))
  return raw / total


def _event_metrics(predicted_event: pd.DataFrame) -> dict[str, Any]:
  predicted_event = predicted_event.sort_values("predictedProbability", ascending=False).reset_index(drop=True)
  actual_winner_code = predicted_event.loc[predicted_event["isWinner"] == 1, "driverCode"].iloc[0]
  predicted_winner_code = predicted_event.iloc[0]["driverCode"]
  winner_rank = int(predicted_event.index[predicted_event["driverCode"] == actual_winner_code][0]) + 1
  return {
    "year": int(predicted_event.iloc[0]["year"]),
    "round": int(predicted_event.iloc[0]["round"]),
    "eventName": predicted_event.iloc[0]["eventName"],
    "predictedWinner": predicted_winner_code,
    "actualWinner": actual_winner_code,
    "winnerProbability": round(float(predicted_event.iloc[0]["predictedProbability"]), 4),
    "actualWinnerRank": winner_rank,
    "top3Hit": winner_rank <= 3,
    "top5": predicted_event.head(5)[["driverCode", "predictedProbability"]].to_dict(orient="records"),
  }


def _evaluate_model(dataset: pd.DataFrame, train_start_year: int, test_year: int, model_name: str, model: Any) -> dict[str, Any]:
  event_keys = (
    dataset[dataset["year"] == test_year][["eventOrder", "year", "round"]]
    .drop_duplicates()
    .sort_values("eventOrder")
    .to_dict(orient="records")
  )

  event_results: list[dict[str, Any]] = []
  top1_hits = 0
  top3_hits = 0
  reciprocal_ranks = []

  for event in event_keys:
    train_df = dataset[
      (dataset["year"] >= train_start_year)
      & (dataset["eventOrder"] < event["eventOrder"])
    ].copy()
    test_df = dataset[
      (dataset["year"] == event["year"])
      & (dataset["round"] == event["round"])
    ].copy()
    if train_df.empty or test_df.empty or train_df["isWinner"].sum() < 3:
      continue

    fitted = clone(model)
    fitted.fit(train_df[FEATURE_COLUMNS], train_df["isWinner"])
    probs = _predict_probs(fitted, test_df[FEATURE_COLUMNS])
    scored = test_df.assign(predictedProbability=probs)
    metrics = _event_metrics(scored)
    event_results.append(metrics)
    if metrics["predictedWinner"] == metrics["actualWinner"]:
      top1_hits += 1
    if metrics["top3Hit"]:
      top3_hits += 1
    reciprocal_ranks.append(1.0 / metrics["actualWinnerRank"])

  event_count = len(event_results)
  return {
    "modelName": model_name,
    "eventsTested": event_count,
    "top1Accuracy": round(top1_hits / event_count, 4) if event_count else 0.0,
    "top3Accuracy": round(top3_hits / event_count, 4) if event_count else 0.0,
    "meanReciprocalRank": round(float(np.mean(reciprocal_ranks)), 4) if reciprocal_ranks else 0.0,
    "racePredictions": event_results,
  }


@lru_cache(maxsize=4)
def _backtest_summary(train_start_year: int, test_year: int) -> dict[str, Any]:
  dataset = _build_dataset(train_start_year, test_year)
  models = _candidate_models()
  evaluations = [
    _evaluate_model(dataset, train_start_year, test_year, model_name, model)
    for model_name, model in models.items()
  ]
  ranked = sorted(
    evaluations,
    key=lambda item: (
      item["top1Accuracy"],
      item["top3Accuracy"],
      item["meanReciprocalRank"],
    ),
    reverse=True,
  )
  best = ranked[0]
  return {
    "trainStartYear": train_start_year,
    "testYear": test_year,
    "features": FEATURE_COLUMNS,
    "bestModel": best["modelName"],
    "bestMetrics": {
      "eventsTested": best["eventsTested"],
      "top1Accuracy": best["top1Accuracy"],
      "top3Accuracy": best["top3Accuracy"],
      "meanReciprocalRank": best["meanReciprocalRank"],
    },
    "modelComparisons": [
      {
        "modelName": item["modelName"],
        "eventsTested": item["eventsTested"],
        "top1Accuracy": item["top1Accuracy"],
        "top3Accuracy": item["top3Accuracy"],
        "meanReciprocalRank": item["meanReciprocalRank"],
      }
      for item in ranked
    ],
    "racePredictions": best["racePredictions"],
    "datasetSummary": {
      "rows": int(len(dataset)),
      "trainRows": int(len(dataset[dataset["year"] < test_year])),
      "testRows": int(len(dataset[dataset["year"] == test_year])),
      "drivers": int(dataset["driverCode"].nunique()),
    },
  }


def backtest_model(train_start_year: int = 2018, test_year: int = 2019) -> dict[str, Any]:
  return _backtest_summary(train_start_year, test_year)


def _build_recent_history_for_future(target_year: int, target_round: int, start_year: int) -> pd.DataFrame:
  frames: list[pd.DataFrame] = []
  for event in recent_completed_events(target_year, target_round, start_year=start_year):
    try:
      frames.append(_build_event_frame(event["year"], event["round"]))
    except Exception:
      continue
  if not frames:
    raise ValueError("No recent history available for future prediction.")
  return _add_features(pd.concat(frames, ignore_index=True))


def _best_model_instance_from_backtest(train_start_year: int = 2018, test_year: int = 2019) -> Any:
  summary = _backtest_summary(train_start_year, test_year)
  return clone(_candidate_models()[summary["bestModel"]])


def _candidate_rows_for_future(history: pd.DataFrame, target_event_name: str) -> pd.DataFrame:
  latest = history.sort_values(["eventOrder", "driverCode"]).groupby("driverCode").tail(1).copy()
  same_track = (
    history[history["eventName"] == target_event_name]
    .groupby("driverCode")["finishPosition"]
    .mean()
    .to_dict()
  )
  latest["same_track_finish_avg"] = latest["driverCode"].map(same_track).fillna(DEFAULT_FEATURES["same_track_finish_avg"])
  for column, default_value in DEFAULT_FEATURES.items():
    latest[column] = latest[column].fillna(default_value)
  return latest


async def predict_next_race() -> dict:
  target = future_or_next_event()
  return await predict_event(target["year"], target["round"])


async def predict_event(year: int, round_number: int) -> dict:
  schedule = get_schedule(year)
  row = schedule[schedule["RoundNumber"] == round_number].iloc[0]
  target = {
    "year": year,
    "round": round_number,
    "eventName": str(row["EventName"]),
    "eventDate": str(pd.to_datetime(row["EventDate"]).date()),
    "circuitName": str(row.get("Location") or row["EventName"]),
    "country": str(row.get("Country") or ""),
    "location": str(row.get("Location") or ""),
  }

  weather = await get_race_weather(target["location"])
  start_year = max(2018, year - 2)
  history = _build_recent_history_for_future(year, round_number, start_year)
  candidates = _candidate_rows_for_future(history, target["eventName"])
  model = _best_model_instance_from_backtest()
  model.fit(history[FEATURE_COLUMNS], history["isWinner"])
  probabilities = _predict_probs(model, candidates[FEATURE_COLUMNS])
  ranked = candidates.assign(winProbability=probabilities).sort_values("winProbability", ascending=False).reset_index(drop=True)

  predictions = []
  for idx, (_, candidate) in enumerate(ranked.iterrows(), start=1):
    weather_fit = 1.0 + float(candidate["wet_skill"]) * 0.3 - float(candidate["dnf_rate"]) * 0.2
    predictions.append(
      {
        "rank": idx,
        "driverCode": candidate["driverCode"],
        "fullName": candidate["fullName"],
        "teamName": candidate["teamName"],
        "winProbability": round(float(candidate["winProbability"]), 4),
        "score": round(float(candidate["winProbability"] * 100), 3),
        "recentForm": round(float(26.0 - candidate["recent_finish_avg"]), 3),
        "sameTrackScore": round(float(26.0 - candidate["same_track_finish_avg"]), 3),
        "weatherFit": round(weather_fit, 3),
        "explanation": [
          f"Recent finish average: {candidate['recent_finish_avg']:.2f}",
          f"Season points to date: {candidate['season_points_to_date']:.1f}",
          f"Podium rate: {candidate['podium_rate'] * 100:.0f}%",
          f"Same-track average finish: {candidate['same_track_finish_avg']:.2f}",
        ],
      }
    )

  best = predictions[0]
  second = predictions[1] if len(predictions) > 1 else best
  gap = round(best["winProbability"] - second["winProbability"], 4)
  label = "High" if gap >= 0.12 else "Medium" if gap >= 0.06 else "Tight"
  summary = _backtest_summary(2018, 2019)

  return {
    "target": {
      "year": target["year"],
      "round": target["round"],
      "eventName": target["eventName"],
      "eventDate": target["eventDate"],
      "circuitName": target["circuitName"],
      "country": target["country"],
    },
    "weather": weather,
    "model": {
      "name": summary["bestModel"],
      "trainedSamples": int(len(history)),
      "featureCount": len(FEATURE_COLUMNS),
      "trainYears": sorted(history["year"].unique().tolist()),
    },
    "winner": best,
    "challengers": predictions[1:6],
    "confidenceBand": {
      "winnerVsSecond": gap,
      "label": label,
    },
  }
