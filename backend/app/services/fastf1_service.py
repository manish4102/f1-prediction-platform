from __future__ import annotations

from functools import lru_cache
from typing import Any

import fastf1
import pandas as pd

from app.core.config import CACHE_DIR


fastf1.Cache.enable_cache(str(CACHE_DIR))


@lru_cache(maxsize=32)
def get_schedule(year: int) -> pd.DataFrame:
  return fastf1.get_event_schedule(year)


def load_race_session(year: int, round_number: int) -> Any:
  session = fastf1.get_session(year, round_number, "R")
  session.load(laps=True, telemetry=False, weather=True, messages=False)
  return session


def load_quali_session(year: int, round_number: int) -> Any:
  session = fastf1.get_session(year, round_number, "Q")
  session.load(laps=True, telemetry=False, weather=False, messages=True)
  return session


def future_or_next_event(reference_year: int | None = None) -> dict:
  schedule_years = [reference_year] if reference_year else []
  if not schedule_years:
    schedule_years = [pd.Timestamp.utcnow().year, pd.Timestamp.utcnow().year + 1]

  today = pd.Timestamp.now().normalize()
  for year in schedule_years:
    schedule = get_schedule(year)
    race_events = schedule[schedule["RoundNumber"].fillna(0) > 0].copy()
    race_events["EventDate"] = pd.to_datetime(race_events["EventDate"])
    upcoming = race_events[race_events["EventDate"] >= today].sort_values("EventDate")
    if not upcoming.empty:
      row = upcoming.iloc[0]
      return {
        "year": int(year),
        "round": int(row["RoundNumber"]),
        "eventName": str(row["EventName"]),
        "eventDate": str(row["EventDate"].date()),
        "circuitName": str(row.get("Location") or row.get("CircuitShortName") or row["EventName"]),
        "country": str(row.get("Country") or ""),
        "location": str(row.get("Location") or ""),
      }
  raise ValueError("No upcoming race found in the available schedules.")


def recent_completed_events(until_year: int, until_round: int, start_year: int = 2022) -> list[dict]:
  events: list[dict] = []
  for year in range(start_year, until_year + 1):
    schedule = get_schedule(year)
    race_events = schedule[schedule["RoundNumber"].fillna(0) > 0].copy()
    race_events["EventDate"] = pd.to_datetime(race_events["EventDate"])
    for _, row in race_events.sort_values("RoundNumber").iterrows():
      round_number = int(row["RoundNumber"])
      if year == until_year and round_number >= until_round:
        continue
      events.append(
        {
          "year": year,
          "round": round_number,
          "eventName": str(row["EventName"]),
          "eventDate": str(row["EventDate"].date()),
          "country": str(row.get("Country") or ""),
          "location": str(row.get("Location") or ""),
        }
      )
  return events


def historical_events(start_year: int, end_year: int) -> list[dict]:
  events: list[dict] = []
  for year in range(start_year, end_year + 1):
    schedule = get_schedule(year)
    race_events = schedule[schedule["RoundNumber"].fillna(0) > 0].copy()
    race_events["EventDate"] = pd.to_datetime(race_events["EventDate"])
    for _, row in race_events.sort_values("RoundNumber").iterrows():
      events.append(
        {
          "year": year,
          "round": int(row["RoundNumber"]),
          "eventName": str(row["EventName"]),
          "eventDate": str(row["EventDate"].date()),
          "country": str(row.get("Country") or ""),
          "location": str(row.get("Location") or ""),
        }
      )
  return events
