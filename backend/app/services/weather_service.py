from __future__ import annotations

from typing import Any
import unicodedata

import httpx

from app.core.config import OPEN_METEO_BASE_URL


TRACK_COORDS: dict[str, tuple[float, float]] = {
  "Sakhir": (26.0325, 50.5106),
  "Jeddah": (21.6319, 39.1044),
  "Melbourne": (-37.8497, 144.968),
  "Suzuka": (34.8431, 136.541),
  "Miami": (25.9581, -80.2389),
  "Imola": (44.3439, 11.7167),
  "Monaco": (43.7347, 7.4206),
  "Montreal": (45.5017, -73.5228),
  "Montréal": (45.5017, -73.5228),
  "Silverstone": (52.0786, -1.0169),
  "Spa-Francorchamps": (50.4372, 5.9714),
  "Zandvoort": (52.3888, 4.5409),
  "Monza": (45.6156, 9.2811),
  "Singapore": (1.2914, 103.864),
  "Austin": (30.1328, -97.6411),
  "Mexico City": (19.4042, -99.0907),
  "Sao Paulo": (-23.7011, -46.6972),
  "São Paulo": (-23.7011, -46.6972),
  "Las Vegas": (36.1147, -115.1728),
  "Lusail": (25.49, 51.4542),
  "Yas Marina": (24.4672, 54.6031),
}


def _normalize_location(value: str) -> str:
  normalized = unicodedata.normalize("NFKD", value)
  return "".join(char for char in normalized if not unicodedata.combining(char)).strip()


def _fallback_weather() -> dict[str, Any]:
  return {
    "source": "fallback",
    "airTempC": None,
    "rainProbability": None,
    "windSpeedKph": None,
    "conditionLabel": "Weather unavailable",
  }


async def get_race_weather(location: str) -> dict[str, Any]:
  coords = TRACK_COORDS.get(location) or TRACK_COORDS.get(_normalize_location(location))
  if not coords:
    return _fallback_weather()

  try:
    async with httpx.AsyncClient(timeout=8.0) as client:
      response = await client.get(
        OPEN_METEO_BASE_URL,
        params={
          "latitude": coords[0],
          "longitude": coords[1],
          "current": "temperature_2m,wind_speed_10m,rain",
          "daily": "precipitation_probability_max",
          "forecast_days": 3,
        },
      )
      response.raise_for_status()
      data = response.json()
  except Exception:
    return _fallback_weather()

  current = data.get("current", {})
  daily = data.get("daily", {})
  rain_probability = None
  if daily.get("precipitation_probability_max"):
    rain_probability = float(daily["precipitation_probability_max"][0])

  rain_value = current.get("rain", 0) or 0
  label = "Dry and stable"
  if rain_probability is not None and rain_probability >= 45:
    label = "Possible wet race"
  elif rain_value and float(rain_value) > 0:
    label = "Rain present"

  return {
    "source": "live",
    "airTempC": float(current["temperature_2m"]) if current.get("temperature_2m") is not None else None,
    "rainProbability": rain_probability,
    "windSpeedKph": float(current["wind_speed_10m"]) if current.get("wind_speed_10m") is not None else None,
    "conditionLabel": label,
  }
