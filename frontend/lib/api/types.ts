export interface SeasonSummary {
  year: number;
  rounds: number;
}

export interface WeatherSnapshot {
  source: "live" | "historical" | "fallback";
  airTempC: number | null;
  rainProbability: number | null;
  windSpeedKph: number | null;
  conditionLabel: string;
}

export interface DriverPrediction {
  rank: number;
  driverCode: string;
  fullName: string;
  teamName: string;
  winProbability: number;
  score: number;
  recentForm: number;
  sameTrackScore: number | null;
  weatherFit: number;
  explanation: string[];
}

export interface PredictionResponse {
  target: {
    year: number;
    round: number;
    eventName: string;
    eventDate: string;
    circuitName: string;
    country: string;
  };
  weather: WeatherSnapshot;
  model: {
    name: string;
    trainedSamples: number;
    featureCount: number;
    trainYears: number[];
  };
  winner: DriverPrediction;
  challengers: DriverPrediction[];
  confidenceBand: {
    winnerVsSecond: number;
    label: string;
  };
  snapshot?: {
    mode: "weekly" | "manual";
    generatedAt: string;
    generatedFor: string;
  };
}
