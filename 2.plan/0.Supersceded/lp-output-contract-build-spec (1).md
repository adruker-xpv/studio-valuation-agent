# LP-report output contract – build specification (generic design layer)

The limited partner (LP) report is the product. Everything upstream — monthly statements, the company valuation
workbook, the company file — exists to make each LP report figure reproducible and auditable. This document turns the
handoff ("Valuation Design Agent Handoff: LP-Report-Driven Output Contract") into build steps on top of the existing
pipeline (v7). It contains no company names, amounts or cell locations; those live in each company's file and each
fund's file in SharePoint.

## Glossary
| Term | Meaning |
|---|---|
| Limited partner (LP) report | The quarterly report to the fund's investors: portfolio rows, totals, fund performance, capital activity |
| Field registry | The list of every figure an LP report can show, with its meaning, unit, period and validation rules (generic) |
| Field map | For one fund or company: which workbook cell or source document supplies each registry field (secure) |
| Lineage record | For one figure in one quarter: value, source, calculation, dependencies, validations, status |
| Multiple on invested capital (MOIC) | (Current value + realized proceeds) ÷ invested capital |
| Internal rate of return (IRR) | The annual return implied by dated cash flows; gross = before fund fees and carry, net = after |
| Distributions to paid-in capital (DPI) | Distributions ÷ contributed capital |
| Total value to paid-in capital (TVPI) | (Net asset value + distributions) ÷ contributed capital |
| Net asset value (NAV) | The fund's value of its holdings net of liabilities, from fund accounting |
| Fully diluted (FD) ownership | Ownership counting all options and convertibles; may differ from the ownership a waterfall uses |
| Trailing twelve months (TTM) | Sum of the 12 monthly values ending at the period end |
| Verified / mapped / review_required | Lineage statuses (section 4) |

---

## 1. Principles (and where this deliberately differs from the handoff)
1. **The LP report is the output contract.** Every number it displays is a key output with a lineage record.
2. **Excel computes; Python verifies and documents.** The handoff lists valuation formulas, waterfalls and attribution
   as "deterministic calculations". They already are: they are the analyst's workbook formulas, recalculated by Excel.
   Re-implementing them in Python would create a second valuation model for non-technical owners to maintain and
   reconcile. Instead, the dependency graph is *extracted* from the workbook (formula tracing, already built) and
   Python runs model-independent checks: identities, totals, cross-file agreement and return metrics recomputed from
   dated cash flows.
3. **The workbook's tabs are implementation; the field registry is the architecture.** The registry and lineage
   records stay stable when a workbook layout changes; only the field map is re-onboarded.
4. **Fund-level figures come from fund sources, not company workbooks.** Contributions, distributions, NAV and net
   returns come from fund accounting. They are ingested and reconciled, and net IRR, DPI and TVPI are recomputed from
   the dated cash flows as a check. Fees and carry are not modelled by this system.
5. **Never guess.** A field without proven lineage is `review_required` and stays visible in the report pack.
6. **Cut line.** What the current LP report does not display is not built. Forecasts and benchmarks, if displayed,
   are ingested as given with their source document as lineage (no modelling) until after handover.

## 2. Layer map: handoff → what exists → what to build
| Handoff layer | Exists in v7 | To build | Phase |
|---|---|---|---|
| Source data → normalized inputs | Statement indexing, append-only statement archive, coverage gate | — | done |
| Company-specific adjustments and rules | Rules learned by reproduction, add-back search, analyst overrides, decisions log | Adjustment categories (recruiting, financing, M&A, compensation, setup, other one-time) as labels on add-back lines | A |
| Valuation calculations | The workbook (Excel), recalculated by the Office Script | Archetype tag per company (section 5) | A |
| Carrying value | Key output "fund value" | Map to registry field `company.carrying_value` | A |
| Attribution bridge | Not handled | Identify the workbook's attribution block; gate: components sum to the valuation change | A |
| Fund portfolio aggregation | Not handled | Fund file: the list of portfolio rows; totals gate | B |
| Fund capital activity and cash flows | Not handled | Ingest the fund cash-flow/NAV schedule; recompute net IRR, DPI, TVPI | C |
| LP-report outputs | Evidence pack per company quarter | LP report pack per fund quarter: registry fields, lineage records, gates | B |

## 3. Field registry (generic, shipped with the skill)
One entry per registry field. Optional fields are allowed and never filled by invention.
```yaml
- field_id: company.carrying_value
  scope: company            # company | portfolio_row | portfolio_total | fund
  section: portfolio_summary
  meaning: approved value of the fund's holding at the period end
  unit: currency
  period_role: current      # current | prior | change | projected
  source_domain: company_valuation_workbook
  validation_rules: [carrying_value_reconciliation, fund_row_reconciliation]
  required_when: displayed_in_lp_report
```
The registry covers the handoff's lists: portfolio row (ownership, invested capital, prior and current valuation,
escrow, realized proceeds, new investments, change in value, MOIC, gross IRR, gross DPI), portfolio totals, fund
performance (net IRR, DPI, TVPI), capital activity (contributed, distributions, unfunded), company operating, market,
enterprise and equity, ownership and security, and attribution fields. Ownership is three separate fields:
fully diluted, outstanding or vested, and effective valuation ownership.

## 4. Lineage records and how status is decided (deterministic)
Each quarter writes `lineage.json` (machine) and a Lineage sheet in the evidence pack (people), one record per
displayed field, in the handoff's record format (field id, label, as-of date, value, source type and locator,
calculation id, dependencies, company override id, validation rules, status, review reason).

| Status | Assigned when |
|---|---|
| verified | Value traced to its sources through the workbook's formula graph; every upstream input set by a rule, a date rule, a roll, or a named analyst; this quarter's check passed; the company file has a passing backtest on its current version; all validation rules for the field pass |
| mapped | Traced and checked this quarter, but the company file has not yet passed a backtest, or an upstream value was carried forward and awaits the named period review |
| review_required | Any gap: no field map, an upstream exception, a failed validation, a missing source domain, or an ambiguous meaning (for example, which ownership the report shows) |

The period review (a named reviewer) moves carried-forward items from mapped to verified for that quarter only.

## 5. Valuation archetypes (tag per company, detected from the workbook, confirmed by the analyst)
| Tag | Formula shape found in the workbook |
|---|---|
| ev_ebitda | enterprise value = multiple × adjusted EBITDA |
| weighted_ev_revenue_ebitda | enterprise value = revenue weight × revenue multiple × revenue + EBITDA weight × EBITDA multiple × EBITDA |
| multi_year_average | the operating metric is an average across years |
| held_at_cost / realized / escrow_based | no multiple; value comes from cost, proceeds or escrow records |
| company_specific | anything else, described in words and approved |
The tag decides which validation identities apply; it never replaces the workbook's own formulas.

## 6. Validation gates: how each is implemented
| Gate (handoff id) | Implementation | Phase |
|---|---|---|
| operating_metric_reconciliation | TTM rule reproduces the workbook value from the archive (exists) | done |
| adjustment_reconciliation, adjusted_ebitda_reconciliation | Base EBITDA + add-back lines = adjusted EBITDA (add-back search exists; category totals added) | A |
| multiple_recalculation | Frozen comparables + the workbook's aggregation reproduce the selected multiple (Excel recalculation) | done |
| enterprise_value_recalculation | Identity for the archetype tag, using key-output values | A |
| equity_value_reconciliation | Enterprise value + cash − debt ± the security claims found in the formula = equity value | A |
| carrying_value_reconciliation | The workbook's ownership or waterfall chain reproduces carrying value (Excel); traced in lineage | A |
| attribution_reconciliation | Sum of attribution components = current − prior valuation | A |
| fund_row_reconciliation | Company carrying value = the fund report's current valuation for that row, unless a fund-level treatment is recorded | B |
| portfolio_total_reconciliation | Displayed totals = sum of rows, within the report's rounding | B |
| return_metric_recalculation | MOIC from invested capital and value; IRR recomputed from dated cash flows (XIRR); DPI and TVPI from fund records | B (gross), C (net) |
| forecast_reconciliation | Only if displayed: projected rows sum to the projected total | after handover |

## 7. Retention (unchanged from v7, extended to fund records)
Active detail: rolling TTM or the window a rule needs. Kept permanently: entry values, investment cash flows, prior
approved valuations, cap-table and ownership history, security and vesting history, material adjustments,
methodology and comparable decisions, and every source version needed to reproduce a past output. Restatements are
kept as superseded values. Nothing is deleted automatically.

## 8. Build plan to handover (18 December 2026)
| Phase | Scope | Done when |
|---|---|---|
| A (to early November) | Company row: registry fields for each company row, field map learned from the workbook's LP-report block, archetype tag, add-back categories, equity and attribution gates, lineage records | Every company-row field in the latest LP report has a lineage record for two companies, each backtested |
| B (to late November) | Fund file and LP report pack: portfolio rows from each company's approved quarter, totals gate, fund-row gate, gross MOIC and IRR recomputation | One fund's latest LP report reproduced field by field, with a pack an auditor can follow |
| C (to mid December) | Fund capital activity and net returns ingested from fund accounting, recomputed as a check; remaining companies onboarded | The Q3 2026 LP report: every field verified, mapped or review_required, none missing |
| After handover | Forecasts, benchmarks, PitchBook comparables, narrative drafting from the calculated bridge | — |

## 9. Information needed (secure layer, not this document)
1. The latest LP report for each fund, in the format it is produced (Excel, PDF or PowerPoint), and the tool or
   template used to produce it.
2. Funds and their portfolio rows: which companies sit in which fund, and any company held by more than one fund.
3. How company values reach the LP report today: from each company workbook's LP-report block directly, or through a
   portfolio summary workbook.
4. The fund-level source: fund administrator statements, a fund cash-flow and NAV schedule, or an internal workbook;
   with dated contributions and distributions.
5. Where the prior approved valuation is recorded (the prior LP report, the prior workbook, or fund accounting).
6. Attribution convention: the order of the bridge (for example, multiple first, then operating metric, then net debt)
   and whether the LP report takes it from the company workbook.
7. For each company: archetype (section 5), reporting currency, foreign-exchange source and date if any, and which
   ownership the LP report shows.
8. Realized or escrow positions this year and their source documents.
9. Whether forecasts and benchmarks appear in the current LP report, and who produces them.
10. Units and rounding in the LP report (thousands, decimals), which set the tolerance for totals.
11. What the auditors ask for today (lead sheets, a request list), so the pack matches it.
12. The first quarter the system must produce, and its deadline.
