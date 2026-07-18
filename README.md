# Sports Lights Up NYC Transit

## Why I built this

Throughout this season, the energy in the city was undoubtedly united behind
the Knicks and their run toward the championship. Videos of crowds forming
all across the city took over my social media feeds, and I wondered how the
MTA handled what seemed like a real boost in ridership. I wanted to take real
data from the MTA and see how game days actually impacted our public transit
system.

My hypothesis was that ridership wouldn't be affected much early in the
playoffs, but that by the Eastern Conference Finals and the Finals, there'd be
more ridership later into the night — even on away games, as the city
gathered to watch.

After actually plotting the data, that's not what it shows. The
weekday/weekend trend in ridership turns out to be a much stronger,
deterministic factor on both ridership and estimated revenue than the games
themselves. So a Friday with no game seems to have greater ridership than a Saturday game night citywide. However this is just one look at it with some small data but opened my eyes to the possibilities with visualizing transit info and improving the designs. 

## How it works

**API-first, committed data as fallback.** When you click a day, the site
queries the [MTA Subway Hourly Ridership](https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership/5wq4-mkjj)
API live from your browser (it's public, keyless, and CORS-enabled). If the
API is slow (>6s) or down, the site falls back to the same day pre-built as
JSON in `docs/data/<event>/` — so the map always loads. The browser console
logs which path served each day.

```
events/<event>.yml            # declares a comparison: window, schedule source, map, theme
        │
scripts/build.py              # build-time pipeline (runs on your machine, not in the browser)
  ├─ event.py                 #   loads the yml into an Event
  ├─ sources/mta.py           #   all MTA handling: Socrata fetch + tidy
  └─ sources/schedules/       #   schedule providers: balldontlie (NBA), manual (yml games list)
        │
docs/data/<event>/            # its output: manifest + one compact JSON per day (the fallback)
docs/data/events.json         # index of declared events (drives the dropdown)
        │
docs/                         # the static site
  ├─ sources/mta.js           #   live MTA query from the browser (API-first path)
  └─ index.html, app.js, app.css   # vanilla-JS dashboard; Plotly draws the map + charts
```

**Data handling is organized by category.** Everything MTA lives in one
module per side (`scripts/sources/mta.py` at build time, `docs/sources/mta.js`
at runtime); sport schedules live in `scripts/sources/schedules/`. A future
dataset — earthquakes, weather, flights — is one new module in `sources/`
plus an `events/*.yml` declaring the comparison; the map and controls don't
change.

**Schedules are build-time only.** The [balldontlie](https://www.balldontlie.io)
NBA API needs a secret key (`.env`, never shipped to the browser), and a
season's schedule is tiny and fixed — so games are baked into the event's
manifest at build time. Sports balldontlie doesn't cover (e.g. the World Cup)
hand-author their `games:` list in the yml.

## Reproduce

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env          # add your balldontlie API key
venv/bin/python scripts/build.py --event knicks_2026
python3 -m http.server -d docs
```

## Credits

- **[MTA Subway Hourly Ridership](https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership/5wq4-mkjj)**
  (Socrata dataset `5wq4-mkjj`, data.ny.gov) — every ridership number on the
  map.
- **[balldontlie](https://www.balldontlie.io)** `/v1/games` API — NBA game
  schedules, scores, and matchups.
- **[Plotly.js](https://plotly.com/javascript/)** (loaded via CDN) — draws
  the map and the comparison charts.
- **[CARTO](https://carto.com/basemaps) dark-matter basemap**, built from
  **[OpenStreetMap](https://www.openstreetmap.org/copyright)** data — the map
  tiles underneath the ridership bubbles (attribution shown live on the map).
- Built with **[Claude Code](https://claude.com/claude-code)** (Anthropic) as
  an AI pair-programmer for the data pipeline and dashboard.
