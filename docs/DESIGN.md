# DESIGN.md -- page rules (site/index.html). Edward Tufte, Visual Display of Quantitative Information / Envisioning Information / Beautiful Evidence.

## Principles -> concrete rules
- Data-ink: every pixel carries data or necessary labels. No boxes around charts, no gridlines (or hairline, 10% ink), no backgrounds behind plots, no icons, no decorative colour.
- No chartjunk: no gradients, shadows, 3D, rounded rectangles, pie charts, dual axes.
- Direct labelling: label points/lines in place; no legends unless unavoidable.
- Comparisons: every number shown with its peer context (peer median, percentile, rank). "Compared to what?"
- Small multiples: one strip plot per metric, identical scales per peer group, aligned.
- Sparklines: word-sized trends inline in tables (district COPA/BIA by year).
- Range-frame axes: axis spans data min-max; ticks at min, median, p99, max.
- Layering + separation via weight and value, not colour: ink for data, grey for context, ONE accent (flag) for outliers.
- Tables are graphics too: right-aligned tabular figures, thin rules only between groups, no zebra stripes.
- Integrity: show data vintage per column; show denominators; never truncate an axis to exaggerate; log scale only when labelled.
- Map: district choropleth in greys (sequential, light->dark = flagged rate), flagged count as direct label; no basemap.

## Tokens
- ET Book (Google Fonts unavailable -> load from cdn.jsdelivr.net/npm/et-book or fallback Georgia, serif). Figures: font-variant-numeric: tabular-nums oldstyle-nums in prose, lining in tables.
- Light: paper #fffff8, ink #111, grey #6b6b6b, rule #d9d6c7, accent #a00000 (flag). Dark: paper #151513, ink #eae7da, grey #9a978a, rule #3a3934, accent #ff6b5e.
- All colours as CSS custom properties on :root; none inline elsewhere (tools/checks.sh greps).

## Layout (top to bottom)
1. Title + one-line purpose + data vintage line + caveat ("statistical outliers for review, not findings of wrongdoing").
2. Headline sentence with counts (Tufte "text-table"): N members, N flagged stat, N flagged fixed, $ total, $ overtime.
3. Four small-multiple strip plots (total, OT, complaints, lawsuits): all members as faint ticks, flagged as accent dots, peer median tick.
4. Flagged table: name, title, district, then per metric value + percentile; flag marks (●stat ○fixed). Sort by any column; filter by metric, flag type, district, title; search by name.
5. District map (small) + district table with sparklines.
6. Drill-down panel per member: all metrics vs peer median/p90/p99 as dot-on-range bars, unit, CPDP link, payroll breakdown.
7. Sources + method notes (footnotes / sidenotes in Tufte style).
- Mobile: single column, 16px gutters, no horizontal page scroll (tables scroll inside their own container).
