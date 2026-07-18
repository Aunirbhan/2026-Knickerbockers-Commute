# Build-time pipeline for one event: schedule + MTA pull -> compact JSON under
# docs/data/<event>/ (manifest + one file per day). The live site queries the
# MTA API directly and only falls back to these files — see docs/sources/mta.js.
#
# Usage:
#   python scripts/build.py --event knicks_2026
#   python scripts/build.py --event knicks_2026 --start 2026-04-17 --end 2026-04-20
import argparse
import json

import pandas as pd
from dotenv import load_dotenv

from config import DOCS_DATA_DIR, FARE_ESTIMATE, HOUR_MAX, HOUR_MIN, ROOT
from event import all_events, load_event
from sources import mta
from sources.schedules import get_games

load_dotenv(ROOT / ".env")


def build(event_id, start=None, end=None):
    event = load_event(event_id)
    win_start = start or event.window["start"]
    win_end = end or event.window["end"]

    games = {g.date: g for g in get_games(event)}
    print(f"{event.display_name}: {len(games)} games in schedule")

    print("Fetching MTA data...")
    tidy = mta.fetch(event, win_start, win_end)
    global_max = int(tidy["ridership"].max())

    out_dir = DOCS_DATA_DIR / event.id
    out_dir.mkdir(parents=True, exist_ok=True)

    day_totals = {}
    for date, grp in tidy.groupby("date"):
        stations, index = [], {}
        for (name, lat, lon), _ in grp.groupby(["station_complex", "latitude", "longitude"]):
            index[name] = len(stations)
            stations.append([name, round(lat, 5), round(lon, 5)])

        frames, hour_totals = {}, {}
        for hour in range(HOUR_MIN, HOUR_MAX + 1):
            vals = [0] * len(stations)
            hgrp = grp[grp["hour"] == hour]
            for name, r in zip(hgrp["station_complex"], hgrp["ridership"]):
                vals[index[name]] = int(r)
            frames[str(hour)] = vals
            hour_totals[str(hour)] = int(hgrp["ridership"].sum())

        day_totals[date] = sum(hour_totals.values())
        with open(out_dir / f"{date}.json", "w") as f:
            json.dump(
                {"date": date, "stations": stations, "frames": frames, "hourTotals": hour_totals},
                f,
                separators=(",", ":"),
            )

    days = []
    for d in pd.date_range(win_start, win_end, freq="D"):
        date = d.strftime("%Y-%m-%d")
        g = games.get(date)
        if g is None:
            day_type, matchup, detail, colors = "No game", "", "", []
        else:
            day_type = {True: "Home game", False: "Away game"}.get(g.home, "Game")
            matchup, detail, colors = g.matchup, g.detail, g.colors
        days.append(
            {
                "date": date,
                "dow": d.strftime("%a"),
                "label": d.strftime("%a %b %-d"),
                "day_type": day_type,
                "matchup": matchup,
                "detail": detail,
                "colors": colors,
                "total": int(day_totals.get(date, 0)),
                "hasData": date in day_totals,
            }
        )

    manifest = {
        "id": event.id,
        "display_name": event.display_name,
        "map": event.map,
        "theme": event.theme,
        "fare": FARE_ESTIMATE,
        "hours": list(range(HOUR_MIN, HOUR_MAX + 1)),
        "globalMax": global_max,
        "days": days,
    }
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, separators=(",", ":"))

    write_events_index()
    print(f"Wrote {len(day_totals)} day files + manifest -> {out_dir}")
    print(f"Coverage: {min(day_totals)} to {max(day_totals)}; globalMax={global_max:,}")


def write_events_index():
    # The dropdown lists every declared event, built or not (unbuilt ones
    # surface the same "no data" message as before).
    index = []
    for event_id in all_events():
        e = load_event(event_id)
        index.append({"id": e.id, "name": e.display_name})
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DOCS_DATA_DIR / "events.json", "w") as f:
        json.dump(index, f, separators=(",", ":"))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--event", default="knicks_2026")
    p.add_argument("--start")
    p.add_argument("--end")
    a = p.parse_args()
    build(a.event, a.start, a.end)
