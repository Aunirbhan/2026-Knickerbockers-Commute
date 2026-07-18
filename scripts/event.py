# An "event" (events/*.yml) is the plug-in unit: window, schedule source, map view, theme.
from dataclasses import dataclass

import yaml

from config import EVENTS_DIR


@dataclass
class Event:
    id: str
    display_name: str
    sport: str
    schedule_source: str  # "balldontlie" or "manual"
    window: dict  # {start, end} as YYYY-MM-DD
    station_scope: str  # "all_nyc" or a list of station_complex strings
    map: dict  # {center:{lat,lon}, zoom}
    theme: dict
    raw: dict  # full parsed yaml (provider-specific extras)


def load_event(event_id):
    with open(EVENTS_DIR / f"{event_id}.yml") as f:
        cfg = yaml.safe_load(f)
    return Event(
        id=cfg["id"],
        display_name=cfg["display_name"],
        sport=cfg.get("sport", ""),
        schedule_source=cfg["schedule_source"],
        window=cfg["window"],
        station_scope=cfg.get("station_scope", "all_nyc"),
        map=cfg["map"],
        theme=cfg.get("theme", {}),
        raw=cfg,
    )


def all_events():
    return sorted(p.stem for p in EVENTS_DIR.glob("*.yml"))
