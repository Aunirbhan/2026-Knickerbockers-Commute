# 04_build_map.py
#
# What: Renders the centerpiece — an animated Plotly scatter map of hourly
#       ridership at the three MSG-area station complexes, one frame per
#       hour, bubbles sized by ridership and colored by Knicks day type.
#       Writes docs/ridership_map.html.
# Why:  The animation is the whole argument: bubbles that surge on home game
#       nights and not on comparable away/no-game nights show, without any
#       statistics, that the MSG crowd rides the subway.
# Concept to understand: bubble sizes are only comparable BETWEEN frames if
#       the marker sizeref is computed from the global max over all frames.
#       plotly.express does this when the size column spans the full frame —
#       we set it explicitly anyway so the invariant survives any refactor.

from pathlib import Path

import pandas as pd
import plotly.express as px

from config import DAY_TYPE_COLORS, MAP_CENTER, MAP_HEIGHT, MAP_ZOOM

ROOT = Path(__file__).resolve().parent.parent
SIZE_MAX = 45

df = pd.read_csv(ROOT / "data" / "map_dataset.csv", parse_dates=["transit_timestamp"])

# Frame label a viewer can place instantly: "Sat Apr 18 — 6 PM".
df = df.sort_values(["transit_timestamp", "station_complex"])
df["frame"] = df["transit_timestamp"].dt.strftime("%a %b %-d — %-I %p")

# One hover-ready line about the game, blank on no-game days.
def game_line(row):
    if row["day_type"] == "Home game":
        return f"vs {row['opponent']} at MSG — tip {row['tip_ET']} ET"
    if row["day_type"] == "Away game":
        return f"at {row['opponent']} — tip {row['tip_ET']} ET"
    return ""

df["game"] = df.apply(game_line, axis=1)

fig = px.scatter_map(
    df,
    lat="latitude",
    lon="longitude",
    size="ridership",
    size_max=SIZE_MAX,
    color="day_type",
    color_discrete_map=DAY_TYPE_COLORS,
    category_orders={"day_type": list(DAY_TYPE_COLORS)},
    animation_frame="frame",
    hover_name="station_complex",
    hover_data={
        "ridership": ":,",
        "day_type": True,
        "game": True,
        "latitude": False,
        "longitude": False,
        "frame": False,
    },
    map_style="carto-positron",
    center=MAP_CENTER,
    zoom=MAP_ZOOM,
    height=MAP_HEIGHT,
    title="MTA Ridership Around Madison Square Garden — 2026 Knicks Playoff Run",
)

# Pin sizeref to the global max so bubble areas mean the same thing in every
# frame (px already does this; made explicit on purpose).
sizeref = 2.0 * df["ridership"].max() / (SIZE_MAX**2)
fig.update_traces(marker=dict(sizeref=sizeref, sizemin=2))
for frame in fig.frames:
    for trace in frame.data:
        trace.marker.sizeref = sizeref
        trace.marker.sizemin = 2

# Faster playback: 1,100+ hourly frames at the default 500 ms would take
# forever to scrub through.
fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 120
fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 0
fig.layout.sliders[0].currentvalue.prefix = ""
fig.update_layout(legend_title_text="Day type", margin=dict(l=10, r=10, t=60, b=10))

out_path = ROOT / "docs" / "ridership_map.html"
fig.write_html(out_path, include_plotlyjs="cdn")
size_mb = out_path.stat().st_size / 1e6
print(f"Wrote {out_path} ({size_mb:.1f} MB, {len(fig.frames)} frames)")
