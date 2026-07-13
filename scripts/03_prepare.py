# 03_prepare.py
#
# What: Turns the raw API pull into one tidy frame for the map — ridership
#       summed across payment methods, a complete hourly grid with gaps
#       filled as 0, the Knicks schedule merged on, and hours restricted to
#       06:00-23:00. Saves data/map_dataset.csv.
# Why:  A Plotly animation needs every station present in every frame; a
#       missing (hour, station) row would make that bubble vanish for a frame
#       instead of showing zero riders.
# Concept to understand: reindexing to a MultiIndex built from the cartesian
#       product of all hours x all stations is how you make "no row" mean
#       "zero" explicitly instead of silently.

from pathlib import Path

import pandas as pd

from config import HOUR_MAX, HOUR_MIN, SCHEDULE, STATIONS

ROOT = Path(__file__).resolve().parent.parent

raw = pd.read_csv(ROOT / "data" / "raw_ridership.csv")
raw["transit_timestamp"] = pd.to_datetime(raw["transit_timestamp"])

# 1. Sum ridership across payment methods per hour and station.
hourly = (
    raw.groupby(["transit_timestamp", "station_complex"], as_index=False)
    .agg(ridership=("ridership", "sum"))
)

# 2. Reindex to the complete hourly grid so every frame has every station.
#    The grid spans the hours actually present in the data (coverage may end
#    before the window if the dataset lags).
full_hours = pd.date_range(
    hourly["transit_timestamp"].min(), hourly["transit_timestamp"].max(), freq="h"
)
grid = pd.MultiIndex.from_product(
    [full_hours, STATIONS], names=["transit_timestamp", "station_complex"]
)
tidy = (
    hourly.set_index(["transit_timestamp", "station_complex"])
    .reindex(grid, fill_value=0)
    .reset_index()
)

# Re-attach each station's lat/lon (constant per station, so take the first).
coords = raw.groupby("station_complex", as_index=False)[["latitude", "longitude"]].first()
tidy = tidy.merge(coords, on="station_complex", how="left")

# 3. Merge the hardcoded schedule on calendar date.
schedule = pd.DataFrame(SCHEDULE, columns=["date", "tip_ET", "opponent", "location"])
schedule["date"] = pd.to_datetime(schedule["date"]).dt.date

tidy["date"] = tidy["transit_timestamp"].dt.date
tidy = tidy.merge(schedule, on="date", how="left")
tidy["day_type"] = (
    tidy["location"].map({"home": "Home game", "away": "Away game"}).fillna("No game")
)
tidy = tidy.drop(columns=["location"])

# 4. Keep only the waking hours the animation shows.
hour = tidy["transit_timestamp"].dt.hour
tidy = tidy[(hour >= HOUR_MIN) & (hour <= HOUR_MAX)].reset_index(drop=True)

out_path = ROOT / "data" / "map_dataset.csv"
tidy.to_csv(out_path, index=False)
print(f"Saved {len(tidy)} rows to {out_path}")
print(f"Coverage: {tidy['transit_timestamp'].min()} to {tidy['transit_timestamp'].max()}")

# Checkpoint: unique dates per day_type (expect 9 home / 9 away if coverage
# is complete).
by_date = tidy.groupby("day_type")["date"].nunique()
print("\nUnique dates by day_type:")
print(by_date.to_string())
