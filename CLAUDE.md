# CLAUDE.md — Sun Walks

**Scope guard: this project has nothing to do with the pipeline M&A thesis.**

If you are working in this folder, ignore `C:\Claude\Work\CLAUDE.md` and the `00-` to `07-` folders entirely. Do not cross-reference them, do not link to them, do not apply the M&A framing. Nothing from this project should ever be written into those folders.

---

## What this is

A tool that answers one question: **which dog walk should I do on a given date and time, if I want to be in the sun?**

**Location: Canmore, Alberta, Canada. 51.09°N, 115.36°W. Valley floor ~1,300 m. Walks within a 50 km radius.**

The interesting part is that "sunny" is not just the weather. Canmore sits on the floor of the Bow Valley beneath 1,000–1,600 m of relief. In winter the sun is low enough that the south skyline blocks it outright for weeks at a time. A cloudless January afternoon in the wrong part of the valley is still a walk in the shade.

**Two factors combine:**
1. **Geometry** — will terrain block the direct sun at that place and time? (deterministic, computable)
2. **Weather** — will there be any direct sun to block? (forecast, uncertain)

They are reported separately, never blended into one opaque score.

**A third factor gates both: is the walk suitable for a dog at all?** In the Bow Valley this is a severe filter — jurisdiction, leash law, wildlife closures, bears, elk, cougars, and avalanche terrain in winter. It runs first, before any sun analysis.

**The dog is Jasper** — James's dog. Medium-sized, Labrador-type, assumed 6–7 years old `[assumption]`. His profile is the initial filter.

## What this is *for*

**This is a demonstration of method, not a production tool.** Kim's stated purpose is to show how he works through a problem like this — not to build something comprehensive.

That reframe drives real decisions and should not be quietly forgotten:

- **Ten walks, not forty.** Chosen for *contrast*, not coverage — walks that produce differentiated answers demonstrate the method; walks that all agree demonstrate nothing
- **The documentation is part of the deliverable**, not scaffolding for it
- **Explicit assumptions and stated uncertainty are the point**, not caveats bolted on at the end
- Success is *"every number on screen can be explained and defended"*, not *"the answer is definitively correct"*

---

## Current state

Pre-build. Scoping only. No code written, no repo created, no data acquired.

**Repository: `C:\Claude\Work\Sun-Walks\` is the Git repo.** Docs and code live together.

**Time budget: three blocks of 2–3 hours this week.** The plan is cut to fit in `docs/08-three-session-plan.md`, which **supersedes the build order in `03` for week one**. Week-one scope is **five walks, not ten** — the minimum contrast set.

**Sequencing:** session 1 toolchain plus sun position; session 2 the shadow engine, validated on synthetic terrain before any real DEM; session 3 five walks and a map. Deferred: Overpass discovery, geopandas, Streamlit, deployment, rules curation.

**At five walks the dog filter is a spreadsheet, not a program.** The tiered filter in `06` stays as the design; it does not need to be code until there are ~40 walks. Recognising when not to write code is part of what this exercise demonstrates.

**Next step:** session 1 of `docs/08-three-session-plan.md`.

---

## Folder structure

```
Sun-Walks/
  CLAUDE.md                         ← this file
  README.md                         ← project summary, current state
  docs/
    01-data-sources.md              ← every input, licence, verdict
    02-method-and-assumptions.md    ← the sun/shadow maths, approximations
    03-app-design.md                ← stack, structure, UI, scope, build order
    04-cursor-and-github-primer.md  ← beginner walkthrough of the tools
    05-open-questions.md            ← unresolved decisions, ordered by what they block
    06-dog-walk-filter.md           ← Phase 1 spec: Jasper, the contrast set, filter tiers
    07-validation-without-local-knowledge.md  ← how to validate having never been there
    08-three-session-plan.md        ← ⚠ START HERE. What actually fits in 6–9 hours
    09-candidate-walks.md           ← the five walks, sourced, with roles and [verify] flags
    10-session-1-walkthrough.md     ← ✅ DONE 9 Sep 2026. Toolchain setup + friction log
    11-session-2-walkthrough.md     ← the ray march and its tests
    12-verification-register.md     ← ⚠ NEXT ACTION. Everything asserted but unchecked
```

## Progress

**Session 1 complete (9 September 2026).** Python 3.13.15 and Git installed; repo live at `github.com/kimlamza/sun-walks` (private); `src/sun.py` computes solar position for Canmore; **validation test A2 passed** — computed sunrise/sunset matched timeanddate.com to within 1 and 3 minutes, confirming solar position contributes negligible error to the project.

**Known loose end:** Cursor opens as "Cursor Agent" with no editor view, file tree or icon strip. Session 1 was completed in plain PowerShell instead. Timeboxed retry at the start of session 2 — `Ctrl+Shift+E`, then `Ctrl+Shift+P` → "View: Show Explorer". Do not let this consume a block.

**Kim is a complete beginner and has asked for step-by-step instruction.** Give exact commands, expected output, and a checkpoint after each block. Explain what a thing *is* before telling him to type it. Do not assume any prior knowledge of terminals, Git, Python or file paths — and do not skip the "why", since the stated purpose of the project is to understand the code rather than to have it produced.

**Already done:** Cursor installed and signed in with Google; GitHub account created and linked to Cursor. Python and Git are **not** yet installed.

**The five walks:** Grotto Canyon (shade extreme) · Quarry Lake (open valley floor, high skyline) · Grassi Lakes (NE-facing, morning sun) · Montane Traverse (SW-facing, afternoon sun) · Tunnel Mountain (high open, control case). Detail and sources in `docs/09-candidate-walks.md`.

Later this folder becomes the GitHub repository root, with `src/`, `data/` and `tests/` alongside `docs/`.

---

## Standards

- **Lead with recommendation → rationale → risks → what would change the view.**
- **Be critical.** The brief is to pressure-test, not to cheerlead.
- **Every factual claim carries a source or a `[verify]` tag.** Canadian dataset details, park regulations and API shapes all change. Tag them heavily.
- **Draft first, ask second.**
- Kim is a **complete beginner at coding**. Explain the why. No unexplained jargon.

## Build constraints (fixed, from Kim)

- Code written in **Cursor**, not an end-to-end app generator. The point is to understand the code.
- Version control on **GitHub**.
- Platform is **Windows**.

## Key context to carry into any session

1. **The Canmore data problem is inverted from the UK.** Trail centrelines are easy — Parks Canada and Alberta Parks publish open data, and OSM coverage of the Bow Valley is strong. **The rules about those trails are the hard part**: leash law by jurisdiction, seasonal wildlife closures, avalanche terrain ratings. Mostly human-readable web pages, not clean APIs.
2. **Leash is required on trails everywhere within 50 km** — Banff NP, Kananaskis and Canmore alike. Banff enforces to $25,000. Designated off-leash *parks* do exist (Quarry Lake meadow and dog pond, Elk Run, and a Banff townsite dog park) — an earlier draft wrongly said none did. Either way, **do not build off-leash as a ranking axis across trails**; it is a constant "no". `[verify]`
3. **Three jurisdictions, three rule sets, three payment regimes:** Town of Canmore (free), Banff National Park (Parks Canada pass), Kananaskis Country (Kananaskis Conservation Pass). Different rules, different closures. `[verify]`
4. **The winter shadow effect here is severe.** Solar noon elevation at Canmore is ~15.5° at the winter solstice. The south skyline from the valley floor is roughly 20–25°. Estimate: **the noon sun does not clear the ridge from roughly early November to early February** for much of the valley floor. This is the strongest argument for the project. It is a **model output to be cross-checked against independent tools**, not a claim to be checked against experience — see point 5.
5. **Nobody on this project has been to Canmore.** This matters far less than it appears. Terrain shadow is deterministic geometry — sun position is computed exactly, the DEM is a published measurement, and the only thing that can be wrong is the code. **Validate against synthetic test terrains, GRASS/QGIS, PVGIS horizon profiles and public webcams — never against memory.** Full treatment in `docs/07-validation-without-local-knowledge.md`. Local knowledge is needed only for judging whether a walk is *pleasant*, which is what official trail descriptions, guidebooks and James are for.
6. **Wildlife is a first-order dog constraint, not a footnote.** Bears (April–Nov), cougars (year-round), elk (calving May–June, rut Aug–Oct, and habituated/aggressive toward dogs). Seasonal closures follow.
7. **Avalanche terrain is a winter life-safety filter**, not a preference. Avalanche Canada bulletins and ATES ratings. The app flags and defers; it never advises.
8. **DEM must extend ~30 km beyond the walk area** — 1,600 m of relief at 5° sun casts an 18 km shadow. Walk radius 50 km therefore implies a DEM covering ~80 km radius.
9. **Cloud beats terrain on any given day.** No direct beam, no shadow question.
10. **Forecast horizon caps the product at ~14 days**, skill degrades sharply past ~5.
11. **Trees, buildings and structures are out of scope.** Use a DTM (bare earth), not a DSM. Note this matters more here than the UK — the Bow Valley has substantial closed-canopy lodgepole and spruce forest, so forested trails will read sunnier than they are.
12. **"In shadow" does not mean dark.** Word it as "no direct sun".
13. **Evaluate at a single instant, but sample many points along the route** — output a percentage of route in sun, not a yes/no.
14. **Sun matters more here than in the UK for a reason worth stating:** at −20 °C the difference between direct sun and shade is the difference between a pleasant walk and a miserable one. In July it inverts — you want shade for the dog.

---

*Last updated: 2026-09-08*
