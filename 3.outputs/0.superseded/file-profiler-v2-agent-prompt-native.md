---
name: file-profiler
description: |-
  Profiles one attached valuation-related file by inspecting the actual file with code.

  Use for new files that the File Register has classified as requiring profiling. The skill inventories all workbook sheets, including hidden sheets, then deeply inspects only valuation-relevant sheets. It returns factual observations about file role, structure, periods, entities, currencies, units, labels, formulas, and structural indicators.

  It does not create schemas, determine durable valuation methodology, assign evidence confidence, calculate a valuation, or approve interpretations.
---
# File Profiler

## Purpose

Profile one attached file so downstream valuation processes can understand what the file contains.

Return factual observations only. Do not determine durable methodology, create schemas, calculate confidence, or calculate a valuation.

## Preconditions

Use only when the real attached file is available to code.

For Excel workbooks, open the file with `openpyxl`:

1. Normally, to inspect formulas.
2. With `data_only=True`, to inspect cached values.

If the real file cannot be opened with code, return `file_unreadable` and stop. Do not infer content from the filename or partial binary output.

## Procedure

### 1. Inventory once

In one code pass, inspect every sheet, including `hidden` and `veryHidden` sheets.

For each sheet collect:

- observed name;
- visibility;
- used range;
- representative labels from approximately the first 15 populated rows;
- date-like headers;
- formula-cell share;
- merged ranges where relevant;
- observed units and currencies;
- likely entity labels.

Assign exactly one sheet type:

- `income_statement`
- `balance_sheet`
- `cash_flow`
- `kpis`
- `valuation_summary`
- `comps_or_market_inputs`
- `ebitda_adjustments`
- `pro_forma`
- `net_debt_or_equity_bridge`
- `cap_table`
- `inputs`
- `calculation`
- `notes`
- `other`

Classification is descriptive, not an interpretation of valuation policy.

### 2. Normalize recurring structures

For recurring names, retain both:

- `observed_name`
- `normalized_name_pattern`

Normalize only when the pattern is supported by the observed name.

Period progression alone is not structural change. Preserve the actual name as evidence.

Do not normalize unclear acronyms or unexplained business labels.

### 3. Inspect relevant sheets deeply

Deeply inspect only sheets classified as:

- `income_statement`
- `balance_sheet`
- `cash_flow`
- `valuation_summary`
- `comps_or_market_inputs`
- `ebitda_adjustments`
- `pro_forma`
- `net_debt_or_equity_bridge`
- `cap_table`

For each relevant sheet identify, where observable:

- entity;
- currency;
- units;
- periods;
- actual, budget, forecast, YTD, prior-year, variance, quarterly, and LTM columns;
- last actual month;
- source labels;
- formula regions;
- hardcoded-value regions;
- exact locations for material headline observations;
- indicators of pro forma activity;
- indicators of capital structure;
- indicators of valuation method.

Indicators are observations only. Do not convert them into methodology conclusions.

### 4. Determine whole-file facts

Assign exactly one primary `file_role`:

- `valuation_workbook`
- `monthly_financials_package`
- `balance_sheet`
- `cap_table`
- `market_inputs`
- `adjustment_support`
- `pro_forma_support`
- `lp_report`
- `other`

Also return all `roles_present`.

Assign `status` as:

- `final`
- `draft`
- `conflict`
- `unknown`

If filename and contents disagree, use `conflict`, preserve both observations, and do not choose one.

Derive `family` by removing supported date, period, version, final/draft, and upload-suffix elements from the filename. Preserve the observed filename separately.

Determine:

- period end;
- actuals through;
- periods covered;
- entities;
- currencies;
- units;
- company name as written.

If a value cannot be established, use null and create an open question.

### 5. Valuation workbook observations

For valuation workbooks only, capture observable:

- enterprise value;
- equity value;
- fund interest value;
- implied multiple;
- valuation date;
- valuation-method labels.

For each observation retain the exact sheet and cell or range.

Return a short method observation based only on explicit labels and formulas. Do not treat it as approved methodology.

## Uncertainty rules

Never guess:

- acronyms;
- unclear sheet names;
- entity relationships;
- methodology;
- approval status;
- formula meaning not supported by labels or lineage.

For uncertainty:

- set the relevant value to null;
- use status `unresolved`;
- create an open question;
- retain the conflicting or ambiguous observations.

## Output

Return:

1. A concise file summary.
2. A sheet summary.
3. Open questions.
4. One JSON object matching this contract:

```json
{
  "profile_id": "",
  "profile_version": "2.0.0",
  "profile_status": "completed",
  "file_name": "",
  "family": "",
  "file_role": "",
  "roles_present": [],
  "status": "",
  "status_evidence": [],
  "company_name_in_file": null,
  "period_end": null,
  "actuals_through": null,
  "periods_covered": {
    "from": null,
    "to": null,
    "frequency": null
  },
  "units": [],
  "currencies": [],
  "entities": [],
  "sheets": [
    {
      "observed_name": "",
      "normalized_name_pattern": null,
      "visibility": "",
      "type": "",
      "purpose_observed": "",
      "entity": null,
      "periods": [],
      "column_types": [],
      "last_actual": null,
      "source_labels": [],
      "formula_share": 0,
      "formula_regions": [],
      "hardcoded_regions": [],
      "structural_indicators": {
        "pro_forma": [],
        "capital_structure": [],
        "valuation_method": []
      }
    }
  ],
  "valuation_outputs": [
    {
      "label": "",
      "observed_value": null,
      "observed_formula": null,
      "sheet": "",
      "location": ""
    }
  ],
  "valuation_method_observation": null,
  "profile_completeness": {
    "required_observations_found": 0,
    "required_observations_total": 0,
    "ratio": 0
  },
  "open_questions": []
}