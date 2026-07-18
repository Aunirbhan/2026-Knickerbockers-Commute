# All MTA handling: Socrata pull + tidy to one row per (date, hour, station).
# Ridership is summed across payment methods server-side (SoQL sum()+$group),
# which cuts the payload roughly threefold before it leaves data.ny.gov.
import pandas as pd
import requests

from config import HOUR_MAX, HOUR_MIN, MTA_API_URL

PAGE = 50000  # Socrata max rows per request


def fetch(event, start=None, end=None):
    start = start or event.window["start"]
    end = end or event.window["end"]
    where = f"transit_timestamp between '{start}T00:00:00' and '{end}T23:59:59'"
    if isinstance(event.station_scope, list):
        stations = ", ".join(f"'{s}'" for s in event.station_scope)
        where += f" and station_complex in ({stations})"

    rows = []
    offset = 0
    while True:
        params = {
            "$select": "transit_timestamp, station_complex, latitude, longitude, "
            "sum(ridership) as ridership",
            "$where": where,
            "$group": "transit_timestamp, station_complex, latitude, longitude",
            "$order": "transit_timestamp",
            "$limit": PAGE,
            "$offset": offset,
        }
        resp = requests.get(MTA_API_URL, params=params, timeout=180)
        resp.raise_for_status()
        page = resp.json()
        rows.extend(page)
        print(f"  offset {offset}: {len(page)} rows")
        if len(page) < PAGE:
            break
        offset += PAGE

    df = pd.DataFrame(rows)
    for col in ("ridership", "latitude", "longitude"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["transit_timestamp"] = pd.to_datetime(df["transit_timestamp"])
    return _tidy(df)


def _tidy(df):
    df["date"] = df["transit_timestamp"].dt.date.astype(str)
    df["hour"] = df["transit_timestamp"].dt.hour
    df = df[(df["hour"] >= HOUR_MIN) & (df["hour"] <= HOUR_MAX)]

    # Collapse again in case a station-hour arrived split across pages.
    tidy = df.groupby(
        ["date", "hour", "station_complex", "latitude", "longitude"], as_index=False
    ).agg(ridership=("ridership", "sum"))
    tidy["ridership"] = tidy["ridership"].round().astype(int)
    return tidy
