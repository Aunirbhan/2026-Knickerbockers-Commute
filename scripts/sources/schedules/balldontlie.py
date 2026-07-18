# NBA schedules from balldontlie /v1/games. Requires BALLDONTLIE_API_KEY in
# .env — build-time only; the key never reaches the browser.
import os

import requests

from sources.schedules import Game
from sources.schedules.nba_colors import color_for

API = "https://api.balldontlie.io/v1/games"


def get_games(event):
    key = os.environ.get("BALLDONTLIE_API_KEY")
    if not key:
        raise RuntimeError("BALLDONTLIE_API_KEY not set (put it in .env)")

    team_id = event.raw["team_id"]
    params = {
        "team_ids[]": team_id,
        "seasons[]": event.raw["season"],
        "postseason": str(event.raw.get("postseason", True)).lower(),
        "per_page": 100,
    }
    resp = requests.get(API, headers={"Authorization": key}, params=params, timeout=60)
    resp.raise_for_status()

    start, end = event.window["start"], event.window["end"]
    games = []
    for g in resp.json().get("data", []):
        date = g["date"][:10]
        if not (start <= date <= end):
            continue
        home_t, away_t = g["home_team"], g["visitor_team"]
        hs, vs = g.get("home_team_score"), g.get("visitor_team_score")
        score = f" {hs}-{vs}" if hs is not None else ""
        games.append(
            Game(
                date=date,
                matchup=f"{away_t['abbreviation']} @ {home_t['abbreviation']}",
                detail=f"{away_t['full_name']} @ {home_t['full_name']}{score}",
                colors=[color_for(home_t["abbreviation"]), color_for(away_t["abbreviation"])],
                home=home_t["id"] == team_id,
            )
        )
    return sorted(games, key=lambda g: g.date)
