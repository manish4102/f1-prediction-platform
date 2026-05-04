from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = ROOT_DIR / "frontend" / "public" / "data" / "latest-prediction.json"
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
  sys.path.insert(0, str(BACKEND_DIR))

from app.services.prediction_service import predict_next_race


async def main() -> None:
  prediction = await predict_next_race()
  prediction["snapshot"] = {
    "mode": "weekly",
    "generatedAt": datetime.now(timezone.utc).isoformat(),
    "generatedFor": "website",
  }

  SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
  SNAPSHOT_PATH.write_text(json.dumps(prediction, indent=2), encoding="utf-8")
  print(f"Wrote weekly snapshot to {SNAPSHOT_PATH}")


if __name__ == "__main__":
  asyncio.run(main())
