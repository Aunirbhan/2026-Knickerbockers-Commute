# 02_fetch.py
#
# What: Pulls hourly ridership rows for the three verified station complexes
#       over the playoff window from the Socrata API and saves them to
#       data/raw_ridership.csv.
# Why:  One raw, unmodified local copy means every downstream step is
#       reproducible offline and the API is hit exactly once.
# Concept to understand: Socrata caps rows per request, so we paginate with
#       $limit/$offset, ordered by transit_timestamp so pages are stable, and
#       stop when a page comes back short.

import csv
from pathlib import Path

import requests

from config import API_URL, STATIONS, WINDOW_START, WINDOW_END

ROOT = Path(__file__).resolve().parent.parent

PAGE_SIZE = 5000
COLUMNS = [
    "transit_timestamp",
    "station_complex",
    "payment_method",
    "ridership",
    "latitude",
    "longitude",
]

station_list = ", ".join(f"'{s}'" for s in STATIONS)
where = (
    f"station_complex in ({station_list}) "
    f"and transit_timestamp between '{WINDOW_START}' and '{WINDOW_END}'"
)

rows = []
offset = 0
while True:
    params = {
        "$select": ", ".join(COLUMNS),
        "$where": where,
        "$order": "transit_timestamp",
        "$limit": PAGE_SIZE,
        "$offset": offset,
    }
    resp = requests.get(API_URL, params=params, timeout=120)
    resp.raise_for_status()
    page = resp.json()
    rows.extend(page)
    print(f"  offset {offset}: {len(page)} rows")
    if len(page) < PAGE_SIZE:
        break
    offset += PAGE_SIZE

out_path = ROOT / "data" / "raw_ridership.csv"
with open(out_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS)
    writer.writeheader()
    for r in rows:
        writer.writerow({c: r.get(c, "") for c in COLUMNS})

print(f"\nSaved {len(rows)} rows to {out_path}")
if rows:
    stations = sorted({r["station_complex"] for r in rows})
    timestamps = [r["transit_timestamp"] for r in rows]
    print("Station complexes retrieved:")
    for s in stations:
        print(f"  {s}")
    print(f"Min transit_timestamp: {min(timestamps)}")
    print(f"Max transit_timestamp: {max(timestamps)}")
else:
    print("WARNING: zero rows returned — check station strings and window.")
