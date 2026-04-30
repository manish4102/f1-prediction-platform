from __future__ import annotations

from pydantic import BaseModel


class SeasonSummary(BaseModel):
  year: int
  rounds: int


class WeatherSnapshot(BaseModel):
  source: str
  airTempC: float | None
  rainProbability: float | None
  windSpeedKph: float | None
  conditionLabel: str


class DriverPrediction(BaseModel):
  rank: int
  driverCode: str
  fullName: str
  teamName: str
  winProbability: float
  score: float
  recentForm: float
  sameTrackScore: float | None
  weatherFit: float
  explanation: list[str]


class PredictionTarget(BaseModel):
  year: int
  round: int
  eventName: str
  eventDate: str
  circuitName: str
  country: str


class ModelMetadata(BaseModel):
  name: str
  trainedSamples: int
  featureCount: int
  trainYears: list[int]


class ConfidenceBand(BaseModel):
  winnerVsSecond: float
  label: str


class PredictionResponse(BaseModel):
  target: PredictionTarget
  weather: WeatherSnapshot
  model: ModelMetadata
  winner: DriverPrediction
  challengers: list[DriverPrediction]
  confidenceBand: ConfidenceBand

