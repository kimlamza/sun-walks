# Sun Walks

**Which dog walk near Canmore will actually be in the sun.**

## Why

Weather apps tell you it will be sunny. They do not tell you that the trail
you picked sits behind Mount Rundle and will not see direct sunlight until
March.

Canmore's valley floor sits around 1,300 m. Mount Rundle and the Three
Sisters rise about 1,640 m above it. At this latitude the midday sun
reaches roughly **62° above the horizon at midsummer and 15.5° at
midwinter** — while the skyline seen from the valley floor can be anywhere
from 8° to 50°, depending entirely on where you stand.

So in winter the question "will this walk be sunny?" has almost nothing to
do with the weather forecast, and almost everything to do with geometry.

The numbers are not subtle. On a December afternoon:

| Walk | In direct sun |
|---|---|
| Montane Traverse | **99%** |
| Grassi Lakes | **0%** |

Those two are four kilometres apart.

## What it does

Pick a date and a time you want to set off. For each walk it works out:

- **Sunshine** — what fraction of the trail has a clear line to the sun,
  computed by ray-tracing a 30 m elevation model out to 30 km in the sun's
  direction. Reported at the start, the midpoint and the end, because a
  three-hour walk can go from full sun to none
- **Weather** — whether there will be any direct sunlight to block, from
  Environment Canada's forecast. Shown separately and never blended with
  the geometry, because they fail in completely different ways
- **Everything else that decides it** — distance, ascent, how long it
  takes, which park pass you need, whether there is water for the dog,
  seasonal dog restrictions, ice risk, and whether you would finish after
  dark

Then it ranks them and tells you which to do, and why the runner-up lost.

## Running it

```bash
git clone https://github.com/kimlamza/sun-walks.git
cd sun-walks

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac or Linux

pip install -r requirements.txt
streamlit run app.py
```

It opens in your browser. Everything it needs is in the repository —
the skylines are precomputed, so there is no elevation data to download
and no API key to get. Weather is fetched live and needs no key either.

Python 3.13. `pytest` runs the tests.

## What it deliberately does not do

- **Trees.** Terrain shadow only. The Bow Valley has a lot of forest, so
  wooded trails read sunnier than they are. This is the largest known bias
- **Tell you whether a trail is open.** Routes come from OpenStreetMap and
  describe where a trail *runs*, not whether you may currently walk it.
  Closures, flood damage and wildlife warnings change constantly and none
  of it is here. A walk shown at 100% sunlit may be closed
- **Assess safety.** Nothing about avalanche terrain, wildlife or trail
  conditions. The app links to Avalanche Canada, Parks Canada and Alberta
  Parks instead
- **Forecast beyond about two weeks.** Past that it says so rather than
  guessing

Distances, ascents and drive times are desk research, not surveyed fact.

## How much to trust it

The geometry is the solid part. It agrees with the European Commission's
independent horizon calculations to **0.7° RMS** at the valley floor, and
computed sunrise matches published tables to within three minutes.

Precision is roughly **±5 percentage points**, and worse at low sun angles
where small differences flip large areas. A 3-point gap between two walks
means nothing; a 90-point gap is real.

The weather half is far less stable — direct beam readings swing by
hundreds of watts within a single hour. The terrain never moves.

## More detail

`docs/` has the full reasoning: where every dataset comes from and what it
costs, the shadow method and every approximation in it, how the model was
validated by someone who has never been to Canada, and a register of
everything asserted but unverified.

`docs/12-verification-register.md` is the honest summary of what is known
versus assumed.
