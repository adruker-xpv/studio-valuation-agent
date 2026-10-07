# Classifying an input (only for the ids in judgment.json)

| type | use when |
|---|---|
| `financial_statement` | comes from the statements each period (revenue, costs, EBITDA, cash, debt) |
| `assumption` | a judgement input: multiple, discount, weighting, add-back, adjustment factor |
| `prior_period` | carried from the previous valuation |
| `constant` | fixed by definition (unit factors, contractual rates) |
| `carry_forward_event_driven` | changes only on an event: cap table, share counts, options, instrument terms |
| `reference_data` | external market data: comparables, FX tables |
| `uncertain` | no label, or the label and the path disagree. Never guess. |

confidence: `high` = label and path both support the type; `medium` = one of them; `low` = neither, or a flag.
notes: one sentence citing the label and the path. If the item has flags, address them.
