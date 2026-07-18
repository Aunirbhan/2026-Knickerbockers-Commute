# Reads games straight from the event yml's `games:` list — for anything
# balldontlie doesn't cover (soccer / World Cup, etc.).
from sources.schedules import Game


def get_games(event):
    games = []
    for g in event.raw.get("games", []):
        games.append(
            Game(
                date=str(g["date"]),
                matchup=g.get("matchup", ""),
                detail=g.get("detail", g.get("matchup", "")),
                colors=g.get("colors", ["#888888"]),
                home=g.get("home"),
            )
        )
    return sorted(games, key=lambda g: g.date)
