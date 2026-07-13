# config.py
#
# What: Single source of truth for every constant the pipeline shares —
#       verified station names, the date window, day-type colors, and the
#       hardcoded 2026 Knicks playoff schedule.
# Why:  The other scripts must agree exactly on strings like
#       "34 St-Penn Station (A,C,E)"; defining them once prevents a typo in
#       one script from silently filtering the data to zero rows.
# Concept to understand: station_complex values were verified against the live
#       API by 01_stations.py (never guessed). Penn Station is two separate
#       complexes in this dataset — (1,2,3) and (A,C,E) — plus Herald Sq.

API_URL = "https://data.ny.gov/resource/5wq4-mkjj.json"

# Exact station_complex strings as returned by 01_stations.py.
STATIONS = [
    "34 St-Penn Station (1,2,3)",
    "34 St-Penn Station (A,C,E)",
    "34 St-Herald Sq (B,D,F,M,N,Q,R,W)",
]

# Analysis window: the 2026 Knicks playoff run.
WINDOW_START = "2026-04-10T00:00:00"
WINDOW_END = "2026-06-12T23:59:59"

# Hours of day kept for the animation (inclusive). Overnight hours are dead
# and make the scrub drag.
HOUR_MIN = 6
HOUR_MAX = 23

# Day-type colors (fixed by the project brief).
DAY_TYPE_COLORS = {
    "No game": "#4C78A8",
    "Away game": "#F2A900",
    "Home game": "#E4572E",
}

# Map view.
MAP_CENTER = {"lat": 40.7505, "lon": -73.9915}
MAP_ZOOM = 13
MAP_HEIGHT = 650

# 2026 Knicks playoff schedule (verified; hardcoded per project brief).
# Tuples: (date, tip-off ET, opponent, location)
SCHEDULE = [
    ("2026-04-18", "18:00", "Hawks", "home"),
    ("2026-04-20", "20:00", "Hawks", "home"),
    ("2026-04-23", "19:00", "Hawks", "away"),
    ("2026-04-25", "18:00", "Hawks", "away"),
    ("2026-04-28", "20:00", "Hawks", "home"),
    ("2026-04-30", "19:00", "Hawks", "away"),
    ("2026-05-04", "20:00", "76ers", "home"),
    ("2026-05-06", "19:00", "76ers", "home"),
    ("2026-05-08", "19:00", "76ers", "away"),
    ("2026-05-10", "15:30", "76ers", "away"),
    ("2026-05-19", "20:00", "Cavaliers", "home"),
    ("2026-05-21", "20:00", "Cavaliers", "home"),
    ("2026-05-23", "20:00", "Cavaliers", "away"),
    ("2026-05-25", "20:00", "Cavaliers", "away"),
    ("2026-06-03", "20:30", "Spurs", "away"),
    ("2026-06-05", "20:30", "Spurs", "away"),
    ("2026-06-08", "20:30", "Spurs", "home"),
    ("2026-06-10", "20:30", "Spurs", "home"),
]
