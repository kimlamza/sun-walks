# Sun Walks — Canmore, Alberta

Pick the dog walk that will actually be in the sun.

**Location:** Canmore, Alberta (51.09°N, 115.36°W), walks within a 50 km radius — the Bow Valley, Kananaskis Country, and the eastern part of Banff National Park.

## The problem

Weather apps tell you it will be sunny. They do not tell you that the trail you picked sits behind Mount Rundle and will not see direct sun until March.

Canmore's valley floor is around 1,300 m. The peaks around it are not:

| Peak | Summit | Relief above valley |
|---|---|---|
| Mount Rundle | 2,949 m | ~1,640 m |
| Three Sisters (Big Sister) | 2,936 m | ~1,630 m |
| Grotto Mountain | 2,706 m | ~1,400 m |
| Mount Lady Macdonald | 2,606 m | ~1,300 m |
| Ha Ling Peak | 2,407 m | ~1,100 m |

Solar noon at 51.09°N reaches about **62° at the summer solstice and about 15.5° at the winter solstice**. The south skyline seen from the valley floor sits at roughly **20–25°**.

**Estimate: from roughly early November to early February, the midday sun never clears the ridge for much of the valley floor.** Not "it's cloudy" — geometrically below the skyline, on a perfectly clear day. `[verify]` against independent terrain tools; this is exactly what the tool computes properly.

At −20 °C, sun versus shade is the whole quality of the walk.

## What this is for

**A demonstration of method, not a production tool.** The purpose is to show how a problem like this gets worked through — the data sourcing, the assumptions, the honest treatment of uncertainty — not to build something comprehensive.

That drives real decisions: **ten walks, not forty**, chosen for *contrast* rather than coverage; the documentation counts as part of the deliverable; and the success criterion is *"every number on screen can be explained and defended"*, not *"the answer is definitively correct"*.

The dog is **Jasper** — James's dog. Medium-sized, Labrador-type, assumed 6–7 years old `[assumption]`. His profile is the first filter applied.

**Nobody on this project has been to Canmore.** This matters less than it appears: terrain shadow is deterministic geometry, so the model is validated against synthetic test cases, independent implementations (GRASS, QGIS, PVGIS) and public webcams — never against memory. Local knowledge is needed only to judge whether a walk is *pleasant*, which is what official trail descriptions, guidebooks and James are for. See `docs/07-validation-without-local-knowledge.md`.

## What it does

Given a date, a time and a set of candidate walks, it reports for each:

- **Geometry** — what proportion of the route has direct line-of-sight to the sun at that instant, from a terrain model
- **Weather** — whether there will be any direct sunlight to have line-of-sight to
- **Practicalities** — distance, ascent, duration, drive time, which pass you need
- **Confidence** — how much to trust it, driven mainly by forecast lead time

...then ranks them, recommends one, and says why the runner-up lost.

The two factors stay separate. A blended "sunniness score" hides which one drove the answer, and they fail in completely different ways.

## Dog suitability comes first

In the Bow Valley this is not a footnote. Before any sun analysis, walks are filtered on:

- **Jurisdiction and leash law** — Banff National Park is leash-at-all-times, no exceptions; Kananaskis and Canmore differ again
- **Seasonal wildlife closures** — bear activity, elk calving and rut, denning
- **Wildlife risk to dogs** — bears, cougars, elk, coyotes
- **Avalanche terrain** — a winter life-safety filter, flagged not advised on
- **Access passes** — Banff park pass, Kananaskis Conservation Pass

This filter runs first and produces a ten-walk shortlist. The sun engine only ever sees walks that passed it. Spec in `docs/06-dog-walk-filter.md`.

**Off-leash turns out to be effectively unavailable** within 50 km outside the Town of Canmore's designated areas — Banff National Park is leash-at-all-times with no exceptions `[verify]`. So it is recorded as metadata, not used as a ranking axis.

## What it does not do

- Model shade from trees — terrain only. Matters here: the valley has substantial closed-canopy forest, so wooded trails will read sunnier than they are
- Track how sun and shade change over the walk — one instant only
- Answer beyond the forecast horizon (~14 days)
- Give safety advice on avalanche or wildlife. It surfaces the official source and defers

Full list in `docs/03-app-design.md`.

## Status

**Pre-build.** Scoping documents only — no code, no repository, no data.

Time budget is three blocks of 2–3 hours. **Start with `docs/08-three-session-plan.md`** — it cuts the plan to what actually fits, and supersedes the build order in `03` for week one.

Week-one scope is **five walks**, chosen as the minimum contrast set: a shaded valley floor, a south-facing sun trap, an east-facing route, a west-facing route, and one high and open as a control. Walks three and four swapping rank between a 09:00 and a 15:00 query is the output that proves the model works.

## Documents

| File | What it covers |
|---|---|
| `docs/01-data-sources.md` | Every input, source, licence, cleaning needed, verdict |
| `docs/02-method-and-assumptions.md` | Sun position, shadow maths, the timing decision, every approximation |
| `docs/03-app-design.md` | Stack, repository structure, UI, scope boundaries, build order |
| `docs/04-cursor-and-github-primer.md` | Cursor and GitHub from zero |
| `docs/05-open-questions.md` | Unresolved decisions, ordered by what they block |
| `docs/06-dog-walk-filter.md` | Phase 1 spec — Jasper, the contrast set, filter tiers |
| `docs/07-validation-without-local-knowledge.md` | How to validate a shadow model having never been there |
| `docs/08-three-session-plan.md` | **Start here.** What actually fits in 6–9 hours |
| `docs/09-candidate-walks.md` | The five proposed walks, sourced, with roles and open checks |
| `docs/10-session-1-walkthrough.md` | Toolchain setup from zero — completed 9 Sep 2026, with a friction log |
| `docs/11-session-2-walkthrough.md` | **Next action.** The ray march, and the tests that prove it correct |

## Build constraints

Written in Cursor. Version-controlled on GitHub. Windows. No end-to-end app generators.
