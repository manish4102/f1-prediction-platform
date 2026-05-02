from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = Path("/tmp/fastf1-cache") if os.getenv("VERCEL") else ROOT_DIR / "cache"
CACHE_DIR = Path(os.getenv("FASTF1_CACHE_DIR", DEFAULT_CACHE_DIR))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_ORIGINS = [
  origin.strip()
  for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:3000,http://127.0.0.1:3000").split(",")
  if origin.strip()
]
OPEN_METEO_BASE_URL = os.getenv(
  "OPEN_METEO_BASE_URL",
  "https://api.open-meteo.com/v1/forecast",
)
