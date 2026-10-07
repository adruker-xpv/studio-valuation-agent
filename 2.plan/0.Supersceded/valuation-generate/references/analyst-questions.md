# Analyst answers (never asked during a run)

Answers the user already gave go in /app/created/answers.json exactly as given; anything missing uses the
default below and is listed as an ASSUMPTION. Corrections update answers.json and re-run build.

| # | Question | answers.json field | Default |
|---|---|---|---|
| 1 | Company name and valuation date (period end)? | `company`, `period_end` (YYYY-MM-DD) | period end = latest month in the statements |
| 2 | What units are the statements in, and what units should the valuation use? | `source_units`, `report_units` (units / thousands / millions) | units -> thousands |
| 3 | Method: EV/EBITDA multiple, EV/Revenue multiple, and their weights? | `ev_ebitda_multiple`, `ev_revenue_multiple`, `weight_ev_ebitda`, `weight_ev_revenue` | EV/EBITDA only, weight 1 |
| 4 | EBITDA adjustments (add-backs) to include, in report units? | `ebitda_adjustments` | 0 |
| 5 | Illiquidity (or other) discount to equity value? | `illiquidity_discount` (e.g. 0.15) | 0 |
| 6 | XPV fully diluted ownership, and any claims ahead of common equity (preferred, other), in report units? | `ownership_pct`, `other_claims` | ownership 1, claims 0 |

When several statement lines match a concept, the first on the best sheet is used and listed as an
ASSUMPTION. The analyst's correction is recorded in `label_overrides` as `{"revenue": "Net Sales"}`.

answers.json example:
```json
{"company": "Test Co", "period_end": "2026-06-30", "source_units": "units", "report_units": "thousands",
 "ev_ebitda_multiple": 9.5, "ev_revenue_multiple": null, "weight_ev_ebitda": 1, "weight_ev_revenue": 0,
 "ebitda_adjustments": 120, "illiquidity_discount": 0.15, "ownership_pct": 1, "other_claims": 0,
 "label_overrides": {}}
```
