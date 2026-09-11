"""
Sun Walks - which dog walk near Canmore will actually be in the sun?

The interface. It holds no analysis of its own: it collects what you want,
calls into src/, and shows the answer. Everything that decides anything
lives in src/terrain.py, src/duration.py and src/weather.py, where it can
be tested without a browser.

Queries are instant because the skylines were worked out in advance by
precompute_horizons.py. Nothing here ray marches.

Run it with:  streamlit run app.py
"""

from datetime import time as time_of_day

import folium
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src import weather
from src.duration import format_duration, walk_times
from src.evaluate import TIMEZONE, centre_of, evaluate, load_walks

SUN = "#e8a33d"
SHADE = "#7d8ca3"


# ----------------------------------------------------------------- loading

@st.cache_resource
def cached_walks():
    return load_walks()


@st.cache_data(ttl=3600)
def weather_at(lat, lon, when):
    try:
        return weather.at(lat, lon, when)
    except Exception:
        return None


# --------------------------------------------------------------- analysis

# ------------------------------------------------------------------- page

st.set_page_config(page_title="Sun Walks", page_icon="*", layout="wide")

st.title("Sun Walks")
st.caption(
    "Which dog walk near Canmore will actually be in the sun. "
    "Terrain shadow is computed from a 30 m elevation model; "
    "weather comes from Open-Meteo."
)

walks = cached_walks()
if not walks:
    st.error("No horizon profiles found. Run `python precompute_horizons.py`.")
    st.stop()

with st.sidebar:
    st.header("When")
    today = pd.Timestamp.now(tz=TIMEZONE).date()
    chosen_date = st.date_input("Date", today)
    chosen_time = st.time_input("Setting off at", time_of_day(11, 0))

    st.header("What")
    mode = st.radio("Looking for", ["Sun", "Shade"], horizontal=True)
    max_drive = st.slider("Most I'll drive (min)", 5, 60, 40, step=5)
    distance = st.slider("Distance (km)", 0.0, 12.0, (2.0, 10.0), step=0.5)
    max_ascent = st.slider("Most ascent (m)", 0, 600, 500, step=50)
    pace = st.slider("Pace factor", 1.0, 2.0, 1.3, step=0.1,
                     help="1.0 is Naismith's fit walker. Higher is slower - "
                          "dogs stop, people take photographs.")

    st.header("Passes I have")
    has_kananaskis = st.checkbox("Kananaskis Conservation Pass", value=True)
    has_parks = st.checkbox("Parks Canada pass", value=True)

start = pd.Timestamp.combine(chosen_date, chosen_time).tz_localize(TIMEZONE)

# ------------------------------------------------------------- filter them

eligible, excluded = [], []
for walk in walks:
    if walk["drive_min"] > max_drive:
        excluded.append((walk, f"{walk['drive_min']} min drive"))
    elif not distance[0] <= walk["distance_km"] <= distance[1]:
        excluded.append((walk, f"{walk['distance_km']:.1f} km"))
    elif walk["ascent_m"] > max_ascent:
        excluded.append((walk, f"{walk['ascent_m']:.0f} m of ascent"))
    elif walk["pass_required"] == "Kananaskis" and not has_kananaskis:
        excluded.append((walk, "needs a Kananaskis pass"))
    elif walk["pass_required"] == "Parks Canada" and not has_parks:
        excluded.append((walk, "needs a Parks Canada pass"))
    else:
        eligible.append(walk)

if not eligible:
    st.warning("Nothing matches. Loosen the filters in the sidebar.")
    st.stop()

# ------------------------------------------------------------- evaluate

results = []
for walk in eligible:
    begin, middle, finish, hours = walk_times(
        start, walk["distance_km"], walk["ascent_m"], pace
    )
    mid_percent, elevation, azimuth, lit = evaluate(walk, middle)
    lat, lon = centre_of(walk)

    results.append({
        "walk": walk,
        "at": middle,
        "hours": hours,
        "start": evaluate(walk, begin)[0],
        "mid": mid_percent,
        "end": evaluate(walk, finish)[0],
        "elevation": elevation,
        "lit": lit,
        "weather": weather_at(lat, lon, middle),
    })

looking_for_sun = mode == "Sun"
results.sort(
    key=lambda r: (
        -1e9 if r["mid"] is None
        else (-r["mid"] if looking_for_sun else r["mid"])
    )
)

beams = sorted(r["weather"]["dni"] for r in results
               if r["weather"] and r["weather"]["dni"] is not None)
median_beam = beams[len(beams) // 2] if beams else None

# ---------------------------------------------------------- recommendation

best = results[0]
runner_up = results[1] if len(results) > 1 else None

if best["mid"] is None:
    st.error(f"The sun is below the horizon at {best['at']:%H:%M}. "
             "Try a later start.")
else:
    word = "in direct sun" if looking_for_sun else "in shade"
    figure = best["mid"] if looking_for_sun else 100 - best["mid"]

    st.subheader(f"{best['walk']['name']} — {figure:.0f}% {word} "
                 f"at {best['at']:%H:%M}")

    left, right = st.columns([3, 2])
    with left:
        w = best["walk"]
        st.write(
            f"{w['distance_km']:.1f} km, {w['ascent_m']:.0f} m ascent, "
            f"about {format_duration(best['hours'])}, "
            f"{w['drive_min']} min drive. "
            + (f"**{w['pass_required']} pass** needed."
               if w["pass_required"] not in ("none", "verify")
               else "No pass needed.")
        )
        # Falls out of evaluating the end time, and matters more than the
        # sunshine figure: Mount Lady Macdonald takes 4h30, so a 15:00
        # February start finishes over an hour after sunset.
        if best["end"] is None:
            finish = best["at"] + pd.Timedelta(hours=best["hours"] / 2)
            st.error(
                f"**You would finish this walk after dark** — around "
                f"{finish:%H:%M}, with the sun already below the horizon. "
                "Set off earlier, or pick something shorter."
            )

        if w.get("access_note"):
            st.warning(f"**Access:** {w['access_note']}")

        if runner_up and runner_up["mid"] is not None:
            gap = abs(best["mid"] - runner_up["mid"])
            st.write(
                f"*{runner_up['walk']['name']} came second at "
                f"{runner_up['mid']:.0f}%"
                + (" — within the model's precision, so treat them as equal."
                   if gap < 5 else ".")
            )

    with right:
        if median_beam is None:
            st.warning("**Beyond the forecast horizon.** Geometry only — "
                       "I can't tell you whether the sun will be out.")
        elif not weather.shadow_matters(median_beam):
            st.warning(f"**Mostly overcast** — median direct beam "
                       f"{median_beam:.0f} W/m². Terrain shadow makes little "
                       "difference today; choose on drive time instead.")
        else:
            confidence = best["weather"]["confidence"]
            st.success(f"**Direct beam {median_beam:.0f} W/m²** — "
                       f"{weather.describe_beam(median_beam)}. "
                       f"Forecast confidence: {confidence}.")

# ------------------------------------------------------------------- map

st.subheader("Where the sun falls")

centre = np.mean([r["walk"]["points"].mean(axis=0) for r in results], axis=0)
chart = folium.Map(location=list(centre), zoom_start=11,
                   tiles="OpenStreetMap")

for result in results:
    lit = result["lit"]
    for index, (lat, lon) in enumerate(result["walk"]["points"]):
        sunny = lit is not None and bool(lit[index])
        folium.CircleMarker(
            location=[float(lat), float(lon)],
            radius=3,
            color=SUN if sunny else SHADE,
            fill=True,
            fill_opacity=0.85,
            popup=f"{result['walk']['name']} — "
                  f"{'sun' if sunny else 'no direct sun'}",
        ).add_to(chart)

st_folium(chart, height=460, use_container_width=True,
          returned_objects=[])
st.caption("Each dot is a sampled point on a trail. "
           f"Amber = direct sun, grey = no direct sun, at each walk's own "
           "midpoint time.")

# ----------------------------------------------------------------- table

st.subheader("All eligible walks")

table = []
for result in results:
    w = result["walk"]
    weather_note = "—"
    if result["weather"] and result["weather"]["dni"] is not None:
        weather_note = weather.describe_beam(result["weather"]["dni"])

    table.append({
        "Walk": w["name"],
        "Evaluated": f"{result['at']:%H:%M}",
        "Start": "dark" if result["start"] is None
                 else f"{result['start']:.0f}%",
        "Midpoint": "dark" if result["mid"] is None
                    else f"{result['mid']:.0f}%",
        "End": "dark" if result["end"] is None else f"{result['end']:.0f}%",
        "Direct beam": weather_note,
        "km": f"{w['distance_km']:.1f}",
        "Ascent": f"{w['ascent_m']:.0f} m",
        "Takes": format_duration(result["hours"]),
        "Drive": f"{w['drive_min']} min",
        "Pass": w["pass_required"],
        "Water": w.get("water", ""),
        "Access": "⚠" if w.get("access_note") else "",
    })

st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")

if excluded:
    with st.expander(f"{len(excluded)} walks excluded by your filters"):
        for walk, reason in excluded:
            st.write(f"- **{walk['name']}** — {reason}")

# --------------------------------------------------------------- caveats

st.divider()
st.markdown(
    """
**What this does not model.** Terrain shadow only — no trees, buildings,
walls or hedges. The Bow Valley has extensive closed-canopy forest, so
wooded trails read sunnier than they are. This is the largest known bias.

**Precision.** The elevation model is 30 m, so gullies and cliff bands are
unresolved, and reprojection noise puts the floor at roughly **±5
percentage points**. A gap of 3 points between two walks means nothing;
a gap of 90 does.

**"In shadow" is not "dark."** It means no direct sun. Diffuse skylight is
still substantial, and over snow it is bright.

**Three instants, not a simulation.** Each walk is evaluated at its start,
its midpoint and its end — with duration estimated by Naismith's rule.
Conditions between those moments are not modelled.

**Weather is a grid forecast**, and Bow Valley conditions are intensely
local. Direct beam is close to binary and swings fast; the geometry above
is stable, the weather is not. Forecast skill decays sharply past five days
and runs out entirely at sixteen.

**Closures and trail damage are not modelled.** Routes come from
OpenStreetMap and describe where a trail runs, not whether you are
currently allowed to walk it. Flooding, erosion, wildlife closures,
seasonal restrictions and avalanche hazard all change access, sometimes
for years, and none of it appears here. **A walk shown at 100% sunlit may
be closed.** Where a standing restriction is known it is flagged above, but
that list is not maintained — check the trailhead kiosk and the relevant
authority before you go.

**This tool does not assess safety.** It says nothing about avalanche
terrain, wildlife or trail conditions. Check Avalanche Canada, Parks Canada
and Alberta Parks. Trail rules, distances and drive times are desk research
flagged `[verify]`, not surveyed fact.
"""
)
