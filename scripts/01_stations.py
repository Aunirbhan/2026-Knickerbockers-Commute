# 01_stations.py
#
# What: Queries the MTA Hourly Ridership API (Socrata dataset 5wq4-mkjj) for the
#       distinct station_complex values containing "34 St" and prints them.
# Why:  Station names in this dataset are exact strings like
#       "34 St-Penn Station (A,C,E)". Filtering by a guessed name silently
#       returns zero rows, so we verify the real strings once, up front, and
#       hardcode the verified strings into scripts/config.py.
# Concept to understand: SoQL — Socrata's SQL-like query language passed as URL
#       parameters ($select, $where, $group). "SELECT DISTINCT" is expressed by
#       selecting a column and grouping by it.

import requests

API = "https://data.ny.gov/resource/5wq4-mkjj.json"

params = {
    "$select": "station_complex",
    "$where": "station_complex like '%34 St%'",
    "$group": "station_complex",
    "$limit": 100,
}

resp = requests.get(API, params=params, timeout=60)
resp.raise_for_status()
rows = resp.json()

print(f"Distinct station_complex values containing '34 St' ({len(rows)}):\n")
for r in sorted(rows, key=lambda r: r["station_complex"]):
    print(f"  {r['station_complex']!r}")
