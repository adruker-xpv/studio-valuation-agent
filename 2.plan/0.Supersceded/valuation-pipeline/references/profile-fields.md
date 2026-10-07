# Rule format (for "rules" in changes.json)

A rule is written only when the analyst states one the discovery did not find. Text in `said` is never executed.

## The executable rule (the most important part)
```json
"execution": {"operation": "sum_months", "months": 3,
              "source": {"sheet": "Income Statements", "label": "Total Revenue", "role": "current"},
              "scale": 0.001, "sign": 1}
```
| operation | meaning | extra fields |
|---|---|---|
| `value_at` | the value for the period: balances, reported figures | - |
| `sum_months` | sum of N consecutive monthly values ending at the period | `months` |
| `ytd_difference` | YTD(period) - YTD(previous quarter end); first fiscal quarter = YTD(period) | `fiscal_year_start_month` |
| `components` | sum of sub-rules, each with its own `sign` (e.g. several debt lines, revenue minus costs) | `components`: list of rules |

`source.role`: `current` (current-period column), `ytd`, or `prior_year`. Budget and variance columns are
never used. `scale` converts statement units to workbook units (0.001 = statements in units, workbook in
thousands). `sign` is 1 or -1.

## Defaults (use these unless the analyst says otherwise)
| Input type | write_mode | period_rule | missing_source_behavior |
|---|---|---|---|
| statement figures with a discovered rule | `roll_window` (rows of periods) or `replace_period_value` (single cells) | from the rule | `block_and_flag` |
| assumptions (multiples, discounts, factors, weights) | `manual_input` | `not_periodic` | `carry_forward_and_flag` |
| judgment adjustments (add-backs) with no rule | `manual_input` | `not_periodic` | `carry_forward_and_flag` |
| cap table, share counts, instrument terms | `carry_forward_event_driven` | `not_periodic` | `carry_forward_and_flag` |
| anything genuinely unknown | `manual_review` (use only when none of the above fits) | `uncertain` | `block_and_flag` |

With these defaults a refresh never stops for a missing assumption: it carries last period's value and
puts it on the review list. `entity` may be left as UNCERTAIN; it is documentation only.

## write_mode
`replace_period_value` (overwrite the current-period cells), `roll_window` (current period by rule, earlier
periods rolled forward from the base workbook), `carry_forward`, `carry_forward_event_driven`,
`manual_input`, `manual_review` (unknown).

## period_rule
`month`, `quarter_sum_of_months`, `quarter_end_balance`, `ltm_sum`, `ytd`, `ytd_difference`, `point_in_time`,
`not_periodic`, `uncertain`. For roll_window it sets the spacing between cells
(quarterly = 3 months) when earlier cells' periods are inferred from the layout.

## missing_source_behavior
`block_and_flag` (exception; default for financial data), `carry_forward_and_flag`, `manual_input`.

## Concept statuses (set by build_profile.py)
| Status | Meaning |
|---|---|
| EXECUTABLE | a runnable rule that reproduced the workbook |
| EXECUTABLE_UNVERIFIED | an analyst-specified rule not yet reproduced; the replay is its first test |
| MANUAL | manual input or carry-forward |
| EXCEPTION | automated, but no runnable rule: needs an `execution` rule or a different write_mode |

A rule may also set `write_mode`, `period_rule` or `missing_source_behavior` (values below).
