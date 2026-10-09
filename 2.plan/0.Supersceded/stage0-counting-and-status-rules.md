# Stage 0 – counting and status rules (rules R1 / P1 / I1 / C1, build 11.7) – for sign-off before the first Gold run

These rules define what "found", "formula", "dependency", "region", "complete" and each status mean. The code implements
them; changing any rule changes its version (R2, P2 …) and the benchmark reports it as a **method change**, never as an
improvement.

## Glossary
| Term | Meaning |
|---|---|
| Layer 0 / 1 / 2 | What the file physically contains / what software deterministically derives from it / what it means financially |
| Gold workbook | A frozen, approved historical valuation workbook, hash-locked, used only for benchmarking |
| Formula node | A formula cell in the relationship graph |
| Referenced edge | The formula names this cell (directly, in a range, a table, a defined name or a 3-D reference) |
| Contributing edge | Python's re-computation of the formula actually read this cell |
| Material | Reached from the Gold-confirmed output cells (enterprise value, equity value, value to XPV) |
| Hub | A cell so many formulas use (a valuation date, a units cell) that connecting through it would merge unrelated work |
| Region | A connected group of formulas and their inputs once hubs are set aside |
| Sink | A formula no other formula uses |
| Terminal | Where a material path ends: a typed value, an external-workbook value or a data-provider (add-in) value |

## 0. Pre-flight and storage (build 11.5)
A file is read only if it is a non-empty `.xlsx` / `.xlsm` package with a workbook part, under 200 MB (2,000 MB uncompressed).
Legacy `.xls`, encrypted or password-protected, `.xlsb`, damaged and non-workbook files are refused with the fix to apply.
Formula-free areas nothing refers to are read completely when they total at most 300,000 cells; above that they are counted,
not read, and any check that needed them reports NOT_EVALUATED (never "not present").

## 1. Physical counting (Layer 0)
| Item | Counted as | Truth for Gold |
|---|---|---|
| Worksheet | every sheet in the workbook, any visibility | Excel (gold-facts.ts) |
| Populated cell | a cell with a value or a formula (formatting alone does not count) | Excel |
| Formula cell | a cell with a formula: an anchor or a member of a shared (copied) formula | Excel |
| Array / spill result | a cell inside an array or dynamic-array formula's range, other than its anchor: a formula RESULT, never a typed input | standard-library checker |
| Error cell | a cell whose value is an Excel error | Excel |
| Defined name | a non-hidden defined name, workbook- or sheet-scoped | Excel |
| External link | a link record to another workbook | Excel (linked workbooks) |
| Table | an Excel table (ListObject) | Excel |
| Out of scope (counted, not interpreted) | conditional formats, data validations, charts, pivot tables' internal cache | standard-library checker |

**To confirm on the first Gold run** (Excel's conventions decide): whether Excel's formula count includes spilled cells;
whether its name count includes print areas; whether "populated" includes cells holding an empty string.

## 2. Relationship graph (Layer 1, rules R1)
Every formula node carries five independent flags. A path is never cut without one of them saying why.

| Flag | Values | Meaning |
|---|---|---|
| references_extracted | COMPLETE / OVER_APPROXIMATED / UNSUPPORTED / MISSING | all references read / read, but some may not contribute (whole columns, ranges read by INDEX, MATCH, lookups, SUMIF(S), COUNTIF(S), CHOOSE, FILTER …) / could not be read (unknown name or table, unreadable syntax, cells the reader did not hold) / a deleted reference (#REF!) or a missing sheet |
| dynamic_resolution | STATIC / DYNAMIC_RESOLVED / DYNAMIC_UNRESOLVED | no INDIRECT or OFFSET / INDIRECT of a fixed text address, resolved / INDIRECT or OFFSET computed at calculation time |
| location | INTERNAL / EXTERNAL (+ identified or not) | reads another workbook; identified = its file is known from the link record |
| cycle | ACYCLIC / CIRCULAR | on a circular reference (Excel iterates) |
| value_verification | RECOMPUTED / NOT_RECOMPUTED / MISMATCH | Python reproduced Excel's saved value / could not re-compute (not a graph gap) / reproduced a different value |

**Headline per output:** FULL = every formula upstream has complete (or resolved) references and is internal or ends at
an identified external workbook; PARTIAL = over-approximated or circular somewhere; UNKNOWN = missing, unsupported,
dynamically unresolved or an unidentified external reference somewhere. Value verification is reported beside it.

**Material** is computed twice: by reference (every referenced edge) and by contribution (contributing edges where
Python re-computed the formula; otherwise referenced). Both are reported.

**Hub (R1):** a date, or a typed value, used by 20 or more formulas. **Region (R1):** connected formulas and their inputs
without hubs; regions with the same sheets, side by side with the same shape, are one **family** for review. A region of
5 or more formulas not reached from the outputs is `cannot_determine` until the analyst classifies it; smaller ones are
listed. Python never calls a region irrelevant.

## 3. Period evidence (Layer 2, rules P1)
The requested quarter is the **target**; it is never evidence about any cell.

| Evidence | Authority |
|---|---|
| Inside a dated monthly / quarterly block (the block header month) | authoritative |
| A formula summing one block row (the window's end month) | authoritative |
| A single window of one block row reproduces the value (for over-approximated formulas) | authoritative |
| A formula taking one block cell (that month) | authoritative |
| Every input with a determined period is PROVEN for the same month | authoritative |
| The cell's own value is a date | authoritative |
| A declared period near the cell: column header, row header, sheet name | supporting |
| An over-approximated block range (the window it could cover) | supporting |

| Status | Rule |
|---|---|
| PROVEN | authoritative evidence, all evidence agrees, every applicable check ran (checks run are recorded) |
| SUPPORTED | only supporting evidence, all agreeing |
| AMBIGUOUS | inputs from several periods, or block rows ending in different months |
| CONFLICTING | two pieces of evidence give different months (e.g. header December, window ends November) |
| NOT DETERMINABLE | no evidence |

Column roles (Actual / Budget / Variance / prior year / year to date) are recorded beside the period.
**PROVEN but wrong** against Gold is counted separately for every detector: one case means the table above is wrong.

## 4. Terminals
A monthly row is ONE terminal (with its cell count). Each terminal has a **class** and, separately, **source evidence**.
Classes: typed financial data, typed balance-sheet data, EBITDA adjustment input, cap-table/share data,
market/comparable input, FX input, valuation assumption, investment/fund record, date input, external-workbook value,
add-in/provider value, **unresolved**. "Parameter" and "hardcoded" are never classes.

**Pasted-value candidates:** a typed material input whose value has at least 4 significant digits and also comes out of
an unreached formula is a possible provenance match (SUPPORTED, for investigation, never proof). Round numbers are not
searched; unique matches rank first; at most 5 per input and 50 in total.

## 5. Invariants (I1) – consistency, not truth
INV-01 EV = selected multiple × metric (single-multiple methods); INV-02 equity is calculated from EV and its formula
reproduces; INV-03 value to XPV is not negative and not above equity (per-company ratio for FX); INV-04 the metric window is
12 months ending at the metric cell's period; INV-05 EV, equity, value to XPV and the metric share one period; INV-06 no
material formula lacks a saved value; INV-07 no material formula's saved value differs from Python's re-computation;
INV-08 total assets = total liabilities + total equity in every month of a balance-sheet block. Each: HOLDS / VIOLATED /
NOT_APPLICABLE / NOT_EVALUATED. A violated invariant is a gate. Per-company changes are named profiles, recorded in the map.

## 6. Independent answers (build 11.6)
**File contents:** Excel's own export (`excel-export.ts`) of every cell - sheet, cell, formula as Excel shows it, value
(dates as Excel serial numbers), type (number, text, boolean, error) - and, for the first cell of each distinct formula
pattern (R1C1), the cells Excel says it uses. The program writes the same columns; the two are compared cell by cell
(numbers within 1 part in 10^9). A reference the program misses counts as "missed but flagged" only when the program's own
flag explains a missing reference (could not read, deleted, computed at calculation time, another workbook) - never
"over-approximated", which explains only extra references.
**Meaning:** the analyst's form - five key numbers (sheet and the cell holding the number), the first and last month of the
earnings figure, the method, and labelled areas (current quarter's valuation, monthly figures used, old history, scratch,
presentation, not sure). check-form refuses label cells, unknown sheets and badly written months; save-answers records
the answers with the time and their own hash, bound to the workbook's fingerprint.
**Confidently wrong:** a key number, month or labelled-area cell month where the program said PROVEN and the analyst
disagrees. It must be 0.

## 7. Chain-first key numbers (rules C1, build 11.7)
An **EV option** is a formula that is a product of exactly one earnings figure (|value| >= 1,000) and one multiple (0.1 to
100, not labelled a weight), or a weighted sum of such products. Following the formula graph downstream: the **equity
bridge** is an additive formula using EV with a plus sign and at least one other term (never one that subtracts a cell on
EV's own row - that is a comparison); **XPV's value** is the anchor-matched formula downstream of equity, else a product of
equity and a share (0 to 1). Rules, in order, the first that applies being the recorded reason: an Excel error in its
inputs; a count is never a multiple; a product of another chain's equity is an ownership step; the earnings figure ends in
another month; it does not lead to the reported value (when the fund workbook is given); a chain dated to the requested
month beats one of unknown period; a complete chain beats an incomplete one. One survivor: PROVEN if complete and it reaches
the reported value or its earnings figure is proven for the requested month (and no stale value, and not unanchored), else
SUPPORTED. Several: AMBIGUOUS, nothing chosen. A saved value that does not match its formula is flagged, never a rejection.
**Anchor:** the reported value matches a cell within the value's own rounding (26,281,000 -> +/- 500; 26,280,918 -> +/- 1),
directly or through an FX-rate cell; typed matches are copies.

## 8. Passing criteria (milestone 1)
Physical import PASS: every physical count equals Excel's. Material graph PASS: every Gold output found; no silent
omission in the sample; no PROVEN-but-wrong; no false certainty; every Gold material region reached; every formula
carries its flags. Completeness gates (open items, never averaged): outputs not fully known, truncated or circular
material formulas, unreached regions not in the key, unresolved terminals, pasted-value candidates, formulas without saved
values, violated invariants. **Safe to design quarterly generation** only when both pass with no open gates on two structurally different Gold
workbooks and no regression. Numeric thresholds are set with the valuation team after the first Gold run, not before.

Signed off: ____________________ (valuation lead)   ____________________ (Aria)   date ________
