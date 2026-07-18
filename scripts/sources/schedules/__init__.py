# Schedule providers. Each exposes get_games(event) -> list[Game]; the build
# picks one by event.schedule_source. Adding a sport = a new provider module
# or a hand-authored games list in the event yml.
from dataclasses import dataclass


@dataclass
class Game:
    date: str  # YYYY-MM-DD
    matchup: str  # e.g. "ATL @ NYK"
    detail: str  # hover line, e.g. "Atlanta Hawks @ New York Knicks 102-113"
    colors: list  # 1-2 hex strings for the timeline
    home: object  # True/False if the focus team is home; None if N/A


def get_games(event):
    if event.schedule_source == "balldontlie":
        from sources.schedules import balldontlie

        return balldontlie.get_games(event)
    if event.schedule_source == "manual":
        from sources.schedules import manual

        return manual.get_games(event)
    raise ValueError(f"Unknown schedule_source: {event.schedule_source}")
