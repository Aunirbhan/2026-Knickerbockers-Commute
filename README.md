# MTA Ridership Around Madison Square Garden — 2026 Knicks Playoff Run

An animated Plotly map of hourly MTA subway ridership at the station
complexes serving Madison Square Garden — 34 St–Penn Station (1,2,3),
34 St–Penn Station (A,C,E), and 34 St–Herald Sq — across the 2026 Knicks
playoff run (April 10 – June 12, 2026). Bubbles grow with ridership and days
are color-coded: **Home game**, **Away game**, **No game**.

The away games are the control group: identical fan interest, no crowd at
MSG. Home-game nights surge in the post-game hours; comparable away-game and
no-game nights don't. The extra riders are the arena crowd — no statistics
needed, you can see it.

**Live site:** the `docs/` folder is a static site served by GitHub Pages
(`docs/index.html` embeds `docs/ridership_map.html`). It also works locally —
just open `docs/index.html` in a browser.

## Reproduce

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cd scripts
../venv/bin/python 01_stations.py   # verify exact station_complex strings
../venv/bin/python 02_fetch.py      # paginated pull -> data/raw_ridership.csv
../venv/bin/python 03_prepare.py    # tidy hourly frame -> data/map_dataset.csv
../venv/bin/python 04_build_map.py  # -> docs/ridership_map.html
```

`scripts/config.py` is the single source of truth for station names, the
date window, colors, and the hardcoded playoff schedule.

## Data source

[MTA Subway Hourly Ridership](https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership/5wq4-mkjj)
(Socrata dataset `5wq4-mkjj`), queried via the SoQL API — no API key needed
at this volume. Data is provided by the MTA / New York State open data
program. Ridership is summed across payment methods (OMNY + MetroCard).

## Limitations

- **Hourly granularity.** The animation is an hourly scrub, not a real-time
  simulation; a "9 PM" frame is the total for the 9–10 PM hour.
- **Ridership values are estimates.** The MTA derives them from fare data;
  treat them as good approximations, not turnstile-exact counts.
- **Batch update lag.** The dataset updates in batches. This build has full
  coverage through June 12, 2026 (all 18 playoff games); a re-fetch closer to
  the events would have hit missing June data.
- **Other MSG events aren't controlled for.** Concerts and other bookings
  also push riders through Penn Station; the color coding only marks Knicks
  games.

## Licenses

Code: MIT (see `LICENSE`). Writeup and site text: CC-BY 4.0.
Data: provided by MTA via data.ny.gov under its open data terms.
