from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = Path(os.getenv("FASTF1_CACHE_DIR", ROOT_DIR / "cache"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
OPEN_METEO_BASE_URL = os.getenv(
  "OPEN_METEO_BASE_URL",
  "https://api.open-meteo.com/v1/forecast",
)

