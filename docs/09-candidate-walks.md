# 09 — Five candidate walks

Desk research, September 2026. Every figure carries a source or a `[verify]` tag.

**All five are legal for a leashed dog, all within ~30 min drive of Canmore, all within Jasper's range.** Between them they cover three jurisdictions, three pass regimes, and — critically — four genuinely different sun aspects.

---

## The five

| # | Walk | Role in the contrast set | Distance | Ascent | Jurisdiction | Pass | Drive |
|---|---|---|---|---|---|---|---|
| 1 | **Grotto Canyon** | Deep shade extreme | ~7.4 km return | ~100–160 m `[verify]` | Bow Valley PP | Kananaskis | ~15 min |
| 2 | **Quarry Lake** | Valley floor, open — but high skyline | ~1.6–3 km | Negligible | Town of Canmore | **Free** | ~5 min |
| 3 | **Grassi Lakes** | NE-facing — morning sun | ~4 km return | ~200 m | Canmore Nordic Centre PP | Kananaskis | ~10 min |
| 4 | **Montane Traverse Loop** | SW-facing bench — afternoon sun | ~7.4 km | ~380 m | Canmore / Bow Valley Wildland `[verify]` | `[verify]` | ~5 min |
| 5 | **Tunnel Mountain** | High, open — the control case | ~4.5 km return | ~266 m | Banff National Park | Parks Canada | ~25 min |

---

## Why each one earns its slot

### 1. Grotto Canyon — the shade extreme

A narrow slot canyon running into Grotto Mountain, walked along a gravel creek bed. Between Canmore and Exshaw, in Bow Valley Provincial Park.

**Why it's here:** this is the deepest terrain shadow available. Canyon walls block the sun from almost every azimuth, so it should read near-0% sunlit for most of the day, most of the year. If the model does *not* say that, something is wrong.

**Corroboration:** one guide is titled *"A Shaded Canyon Walk for Hot Summer Days"* — independent confirmation of the shade, from people who have been there.

**Dogs:** leashed dogs permitted. ⚠ `[verify]` — one source in the search results claimed pets are *not* allowed, contradicting several others. Check the Alberta Parks page directly before committing.

**Also:** popular winter ice walk, so it is a genuine year-round option.

### 2. Quarry Lake — open ground, high skyline

Flat loop at the southwest edge of Canmore, directly beneath the Ha Ling / Rundle massif. Free, five minutes from town.

**Why it's here:** it is the walk you would *assume* is sunny — open, treeless, no canyon, right in town. But it sits at the foot of a 1,100 m wall. **If the model shows it shaded in December while looking open on the map, that is the single clearest demonstration of why this tool exists.** Openness is not sunniness; skyline height is.

**Dogs:** two official off-leash zones — the meadow and the dog pond. The 1 km loop trail has been changed back to on-leash `[verify] current status`. Maximum three off-leash dogs per person under the updated animal control bylaw. Off-leash fines start at $100.

**Caution:** parts of the site are wildlife corridor and habitat patch, and elk use the area. Relevant to Jasper.

**Note:** short. Pair it with adjacent Nordic Centre trails if 1.6 km is too little.

### 3. Grassi Lakes — morning sun, afternoon shade

Gentle forested ascent to turquoise lakes below Ha Ling Peak, in Canmore Nordic Centre Provincial Park.

**Why it's here:** it sits on the **northeast-facing** flank of the valley, under the Lawrence Grassi / Ha Ling massif. Expected profile: sun early, then blocked from mid-morning onward as the sun swings south and west behind the wall above. That makes it the **morning half of the east/west pair**.

**Dogs:** leashed dogs welcome.

**Note:** two routes exist — the "interpretive" (easier, wider) and the "upper/steeper" trail. Alberta Parks reports them separately. Pick one and record which.

### 4. Montane Traverse Loop — afternoon sun

Loop on the benchlands above Canmore, on the lower slopes of Mount Lady Macdonald.

**Why it's here:** the mirror image of Grassi Lakes. It sits on the **southwest-facing** side of the valley, elevated above the floor, looking across at Rundle. Two things should follow: it catches the *afternoon* sun, and because it is raised above the valley floor, the massif opposite subtends a smaller angle — so it should hold winter sun better than anything at valley level.

**This is the walk most likely to win a January query, and Grassi Lakes is most likely to win a 09:00 one. That swap is the demonstration.**

**Dogs:** leashed dogs welcome.

`[verify]` exact jurisdiction and whether a Kananaskis pass applies at the trailhead — the boundary between Town of Canmore land and Bow Valley Wildland Provincial Park runs through this area.

### 5. Tunnel Mountain — the control

Short switchbacking climb to a low, open summit above Banff townsite. Isolated small peak with sweeping views across the Bow Valley to Rundle.

**Why it's here:** it is a **standalone hill**, so its horizon is low in every direction. It should read close to 100% sunlit whenever the sun is above the horizon, in any season. **If it does not, the model is broken.** That makes it a live self-test running on every query, not just a walk.

It is also the only one of the five in Banff National Park, which exercises the third jurisdiction and the Parks Canada pass path.

**Dogs:** leashed at all times — this is national park law, with fines up to $25,000 and active enforcement.

---

---

## ⚠ Measured results, 10 September 2026

Trail geometry from OpenStreetMap, terrain from Copernicus GLO-30, per-point ray march at the sun's actual bearing.

**Percentage of trail points with a clear line to the sun:**

| Walk | 21 Dec, 10:30 | 21 Dec, 15:30 | 21 Jun, 09:00 | 21 Jun, 14:00 |
|---|---|---|---|---|
| Montane Traverse | 63% | **100%** | 100% | 100% |
| Tunnel Mountain | 0% | 69% | 95% | 100% |
| Grotto Canyon | 18% | 28% | 89% | 100% |
| Grassi Lakes | **0%** | **4%** | 100% | 100% |

### What held

**Montane Traverse is the winter walk, decisively.** **Grassi Lakes gets essentially no direct sun all winter** — consistent with a measured 41.7° skyline beneath Ha Ling. **Grotto Canyon is deeply shaded in winter.** All three aspect inferences confirmed.

### What did not hold — and both errors were mine, not the model's

**1. Tunnel Mountain is not a valid control.** I described it as "a standalone hill, so its horizon is low in every direction… if it does not read ~100% sunlit, the model is broken." It reads 0% at 10:30 on the solstice, and the model is right.

Tunnel Mountain is a **1,690 m hill inside a valley** between Rundle (2,949 m) and Sulphur (2,451 m). Its horizon is not low. At 10:30 the sun sits 4.6° up on bearing 137°, where Rundle's ridge subtends roughly 22°. Compounding it, the trail is mostly switchbacking *flanks*, not summit.

**No real walk can serve as a control in the Rockies.** The flat-plane case in `tests/test_terrain.py` already is one, and is better — it cannot be confounded by geography.

**2. There is no morning/afternoon swap in winter.** The predicted east/west pair reversing between 09:00 and 15:00 does not happen: Montane wins both.

**In midwinter at 51°N the sun's entire daily arc spans roughly 128° to 232°** — about 100° of azimuth, all southern. The sun rises south-east and sets south-west; there is no morning east sun in December. A north-east-facing trail is shaded whatever the hour. In midsummer the arc runs roughly 50° to 310°, over 260°, and Grassi Lakes duly reaches 100% at 09:00.

**So: in winter, aspect dominates and time of day barely matters. In summer, time of day dominates.** The swap prediction was UK-latitude reasoning applied where the winter sun hardly moves.

**3. Summer is uninteresting.** Midsummer afternoon returns 100% for every walk — the sun at 62° clears everything. This is a winter instrument, which settles Q3 in `05-open-questions.md`.

### Still outstanding

**Quarry Lake is not in OpenStreetMap** under that name as a walkable path — it is likely mapped as water with unnamed paths around it. Needs fetching by proximity to coordinates rather than by name.

---

## What this set covers

| Dimension | Spread achieved |
|---|---|
| **Aspect** | Canyon (all azimuths blocked), NE-facing, SW-facing, valley floor open, isolated summit |
| **Jurisdiction** | Town of Canmore, Alberta Parks ×2 (Bow Valley PP, Nordic Centre PP), Banff NP |
| **Pass** | Free / Kananaskis Conservation Pass ($15 day, $90 year) / Parks Canada |
| **Distance** | 1.6 km to 7.4 km |
| **Ascent** | ~0 m to ~380 m |
| **Drive** | 5 to 25 minutes |
| **Season** | All five are year-round walks |

Every one is comfortably inside Jasper's envelope — no scrambling, no exposure, no sustained sharp scree, nothing over 400 m of gain.

---

## What the desk research could *not* establish

**No published source gives sun-and-shade patterns for these trails by date and time.** Searches for Canmore winter shadow patterns returned general climate data — December averages 26% possible sunshine and about 126 hours of sun `[verify]` — and one passing remark that the East End of Rundle "receives plenty of sunlight to melt snow faster than other peaks". Nothing usable.

**That is the finding, not a gap.** The question this tool answers has not been answered publicly anywhere, which is a reasonable justification for building it. It also means the aspect reasoning above — which walk gets morning versus afternoon sun — is **my inference from valley geometry, not a sourced claim.** It is a prediction the model should test, and one of the model's outputs will be whether I was right.

Flagged accordingly: every "expected sun profile" in this document is `[unverified inference]`.

---

## Correction to an earlier claim

I previously stated that off-leash is "effectively unavailable within 50 km outside designated Town of Canmore areas". **That was too strong on one point and correct on the other:**

- ✅ **Correct:** off-leash is not permitted on trails anywhere in the area — Banff NP, Kananaskis and Canmore all require a leash on trail
- ❌ **Too strong:** designated off-leash *parks* do exist — Quarry Lake has two official off-leash zones, Canmore has other off-leash areas including Elk Run, and **Banff townsite has its own off-leash dog park**

The practical conclusion is unchanged — off-leash is not a useful ranking axis across hiking trails — but "no off-leash anywhere in Banff National Park" was wrong and is corrected in `06-dog-walk-filter.md`.

---

## Before session 3

- `[verify]` **Grotto Canyon dog policy** on the Alberta Parks page — sources conflict
- `[verify]` **Montane Traverse jurisdiction and pass** at the trailhead
- `[verify]` **Quarry Lake loop on-leash status** — it was being changed back
- Check current Alberta Parks and Parks Canada advisories for all five
- Decide Grassi Lakes interpretive vs upper route
- Draw all five at [gpx.studio](https://gpx.studio) and export GPX

---

## Sources

- [Grotto Canyon: A Shaded Canyon Walk for Hot Summer Days — Play Canmore](https://playcanmore.com/grotto-canyon-hike/)
- [Grotto Canyon Trail — AllTrails](https://www.alltrails.com/trail/canada/alberta/grotto-canyon-trail)
- [Grotto Canyon Hike — 10Adventures](https://www.10adventures.com/hikes/canmore/grotto-canyon/)
- [Grassi Lakes Upper — Alberta Parks trail report](https://www.albertaparks.ca/parks/kananaskis/kananaskis-country/advisories-and-public-safety/trail-reports/canmore-and-area/grassi-lakes-upper/)
- [Grassi Lakes Day Use — Canmore Nordic Centre PP, Alberta Parks](https://www.albertaparks.ca/parks/kananaskis/canmore-nordic-centre-pp/park-facilities/day-use/grassi-lakes/)
- [Montane Traverse Loop — AllTrails](https://www.alltrails.com/trail/canada/alberta/montane-traverse-loop)
- [Benchlands Ridge — AllTrails](https://www.alltrails.com/trail/canada/alberta/benchlands-ridge)
- [Tunnel Mountain Summit — AllTrails](https://www.alltrails.com/trail/canada/alberta/tunnel-mountain-summit)
- [Tunnel Mountain Hike — The Banff Guide](https://thebanffguide.com/tunnel-mountain-hike-banff-summit-trail-guide/)
- [Keep dogs on leash — Banff National Park, Parks Canada](https://parks.canada.ca/pn-np/ab/banff/visit/faune-wildlife/chiens-dogs)
- [Park regulations — Banff National Park, Parks Canada](https://parks.canada.ca/pn-np/ab/banff/securite-safety/regles-rules)
- [Kananaskis Conservation Pass — Alberta.ca](https://www.alberta.ca/kananaskis-conservation-pass)
- [A Guide to Purchasing a Kananaskis Conservation Pass — The Banff Blog](https://thebanffblog.com/kananaskis-conservation-pass/)
- [Pet Owners — Town of Canmore](https://www.canmore.ca/your-community/residential-services/pets)
- [Canmore caps off-leash dogs at Quarry Lake — Rocky Mountain Outlook](https://www.rmoutlook.com/canmore/canmore-caps-off-leash-dogs-at-quarry-lake-increases-fines-for-off-leash-dogs-8461883)
- [Quarry Lake off-leash loop trail changing to on-leash — Rocky Mountain Outlook](https://www.rmoutlook.com/canmore/quarry-lake-off-leash-dog-park-loop-trail-changing-to-on-leash-1990516)
- [Quarry Lake Park hikes and dog walks](https://www.quarrylakecanmore.ca/quarry_lake_park_hikes_dog_walks.html)
- [Ultimate Guide: Dog-Friendly Getaway in Canmore and Kananaskis — Explore Canmore](https://www.explorecanmore.ca/blog/ultimate-guide-dog-friendly-getaway-in-canmore-and-kananaskis/)
- [Canmore Weather in Each Season — Beautiful Canmore](https://beautifulcanmore.com/canmore-weather/)
