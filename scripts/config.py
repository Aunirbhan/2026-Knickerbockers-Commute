from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS_DIR = ROOT / "events"
DOCS_DATA_DIR = ROOT / "docs" / "data"

MTA_API_URL = "https://data.ny.gov/resource/5wq4-mkjj.json"
FARE_ESTIMATE = 2.90  # USD flat estimate; the dataset has no revenue field
HOUR_MIN, HOUR_MAX = 6, 23  # waking hours shown on the map
