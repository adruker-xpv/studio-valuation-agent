# map_financials.py - maps statement lines to generic concepts and selects the LTM / period-end values
# Usage: python map_financials.py --sources-index sources_index.json [--answers answers.json] --out mapping.json
# Deterministic: concept library synonyms (references/concept-library.json), sheet hints, header dates.
# Prints MAPPING STATUS: READY | NEEDS_ANSWERS, and the exact questions that remain.
import sys, os, re, json, argparse
from collections import defaultdict
from openpyxl.utils import column_index_from_string as col_idx
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wbutil import parse_period, parse_period_end, month_index, build_series, ym_to_i, i_to_ym

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "concept-library.json")


def norm(s):
    s = str(s).lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^total ", "", s)
    return s


def split_ref(cell):
    col = "".join(ch for ch in cell if ch.isalpha())
    return col_idx(col), int(cell[len(col):])


def main(a):
    lib = json.load(open(LIB, encoding="utf-8"))
    idx = json.load(open(a.sources_index, encoding="utf-8"))
    ans = json.load(open(a.answers, encoding="utf-8")) if a.answers else {}
    overrides = {k: norm(v) for k, v in (ans.get("label_overrides") or {}).items()}
    fper = {f["name"]: ym_to_i(parse_period(f["statement_period"])) for f in idx.get("files", [])
            if isinstance(f, dict) and f.get("statement_period")}
    series = build_series(idx["values"], fper)
    # one "row" per series of actuals (current-period columns), across all files
    rows, labels = {}, {}
    for (sh, lb, role), s_ in series.items():
        if role != "current":
            continue
        any_e = next(iter(s_.values()))
        k = (any_e["file"] if len({e["file"] for e in s_.values()}) == 1 else "(several files)", any_e["sheet"], lb)
        rows[k] = [(i, e) for i, e in sorted(s_.items())]
        labels[k] = norm(any_e["label"])

    dated_all = [i_to_ym(i) for s_ in series.values() for i in s_] + [i_to_ym(i) for i in fper.values()]
    if ans.get("period_end"):
        pe, pe_src = parse_period_end(ans["period_end"]), "answers.json"
    elif dated_all:
        pe, pe_src = max(dated_all, key=month_index), "latest dated column (confirm)"
    else:
        print("MAPPING STATUS: NEEDS_ANSWERS\n- no dated columns found; question: what is the period end?")
        return 3
    pe_i = month_index(pe)

    def hint_score(kind, sheet):
        s = norm(sheet)
        return 1 if any(h == s or h in s.split() or (len(h) > 3 and h in s) for h in lib["sheet_hints"][kind]) else 0

    owner = {}                                   # label -> concepts that list it as an exact synonym
    for con in lib["concepts"]:
        for x in con["synonyms"]:
            owner.setdefault(norm(x), set()).add(con["id"])
    out, questions, assumptions = {}, [], []
    for con in lib["concepts"]:
        syn = [norm(x) for x in con["synonyms"]]
        if con["id"] in overrides:
            exact = [k for k, l in labels.items() if l == overrides[con["id"]]]
            contains = []
        else:
            exact = [k for k, l in labels.items() if l in syn]
            contains = [k for k, l in labels.items() if k not in exact and not (owner.get(l, set()) - {con["id"]}) and
                        any(re.search(rf"(^| ){re.escape(s)}( |$)", l) for s in syn if len(s) > 3)]
        cands, mtype = (exact, "exact") if exact else (contains, "contains")
        if con["id"] == "debt" and con["id"] not in overrides:
            totals = [k for k in exact if labels[k] == "debt"]          # 'Debt' or 'Total debt'
            cands = totals if len(totals) == 1 else sorted(set(exact) | set(contains))
            mtype = "exact" if len(totals) == 1 else ("sum_of_components" if len(cands) > 1 else mtype)
        if len(cands) > 1:
            best = max(hint_score(con["kind"], k[1]) for k in cands)
            cands = [k for k in cands if hint_score(con["kind"], k[1]) == best]
        if len(cands) > 1 and con["id"] == "debt":
            pass                                   # several debt lines: added up, flagged in the summary
        elif len(cands) > 1:
            first = sorted(cands, key=lambda k: ("#" in k[2], k[1], k[2]))
            assumptions.append(f"{con['name']}: several lines match (" + ", ".join(f"'{rows[k][0][1]['label']}' on {k[1]}" for k in first)
                               + f"); used '{rows[first[0]][0][1]['label']}' on {first[0][1]}. Confirm, or name the right line.")
            cands = first[:1]
        if not cands:
            out[con["id"]] = {"status": "missing"}
            continue
        picks = []
        for k in cands:
            items = [(i_to_ym(i), i, v) for i, v in rows[k] if i <= pe_i]
            if not items:
                continue
            if con["kind"] == "balance":
                if month_index(items[-1][0]) != pe_i:
                    continue
                sel, freq = [items[-1]], "point"
            else:
                steps = [month_index(b[0]) - month_index(a_[0]) for a_, b in zip(items, items[1:])]
                freq = max(set(steps[-11:]), key=steps[-11:].count) if steps else None
                n = {1: 12, 3: 4, 12: 1}.get(freq)
                if not n or len(items) < n or month_index(items[-1][0]) != pe_i:
                    continue
                sel = items[-n:]
                ms = [month_index(p) for p, _, _ in sel]
                if any(b - a_ != freq for a_, b in zip(ms, ms[1:])):
                    continue
            picks.append({"file": k[0], "sheet": k[1], "row": sel[-1][2].get("row"), "label": rows[k][0][1]["label"],
                          "frequency": {1: "monthly", 3: "quarterly", 12: "annual", "point": "period end"}[freq],
                          "cells": [f"{v['file']} / {v['cell']}" for _, _, v in sel], "periods": [v["period"] for _, _, v in sel],
                          "values": [v["value"] for _, _, v in sel]})
        if not picks:
            avail = sorted({i for k in cands for i, _ in rows[k] if i <= pe_i})
            span = f"{i_to_ym(avail[0])[0]}-{i_to_ym(avail[0])[1]:02d}..{i_to_ym(avail[-1])[0]}-{i_to_ym(avail[-1])[1]:02d}" if avail else "none"
            need = "a value at the period end" if con["kind"] == "balance" else "12 consecutive months (or 4 quarters)"
            out[con["id"]] = {"status": "missing", "reason": f"line found; needs {need} ending {pe[0]}-{pe[1]:02d}, "
                              f"statements cover {len(avail)} periods ({span})", "lines": [rows[k][0][1]["label"] for k in cands]}
            continue
        out[con["id"]] = {"status": "mapped", "match": "override" if con["id"] in overrides else mtype,
                          "kind": con["kind"], "cost": con["cost"], "name": con["name"], "lines": picks}

    # EBITDA route
    route = None
    for combo in lib["ebitda_derivation_order"]:
        if all(out.get(c, {}).get("status") == "mapped" for c in combo):
            route = combo
            break
    short = [m_ for m_ in out.values() if m_.get("reason", "").startswith("line found; needs 12")]
    if route is None and short:
        questions.append(f"The statements do not cover twelve months ({short[0]['reason'].split('statements cover ')[1]}). "
                         "Upload the missing monthly statements, or give LTM revenue and LTM EBITDA directly.")
    elif route is None:
        questions.append("No EBITDA line and no complete set of lines to derive it (EBIT + D&A, or revenue - COGS - operating "
                         "expenses). Which statement lines should be used?")
    bridge = "net_debt" if out.get("net_debt", {}).get("status") == "mapped" else (
        "debt_less_cash" if all(out.get(c, {}).get("status") == "mapped" for c in ("debt", "cash")) else None)
    if bridge is None:
        questions.append("No net debt, or debt and cash, at the period end. What is net debt at the period end (report units)?")
    need_rev = bool(ans.get("ev_revenue_multiple"))
    if need_rev and out.get("revenue", {}).get("status") != "mapped":
        questions.append("EV/Revenue is used but no revenue line was found. Which line is revenue?")
    for f, q in [("ev_ebitda_multiple", "EV/EBITDA multiple not given: left blank in Inputs (EV shows 0 until it is entered)."),
                 ("ownership_pct", "XPV ownership not given: 1 (100%) used."),
                 ("illiquidity_discount", "Illiquidity discount not given: 0 used."),
                 ("source_units", "Statement units not given: 'units' assumed, valuation in thousands."),
                 ("ebitda_adjustments", "EBITDA adjustments not given: 0 used."),
                 ("other_claims", "Claims ahead of common equity not given: 0 used.")]:
        if f not in ans:
            assumptions.append(q)
    if ans.get("period_end") is None:
        assumptions.append(f"Period end not given: {pe[0]}-{pe[1]:02d} used (latest dated statement).")
    status = "CANNOT_BUILD" if questions else ("READY_WITH_ASSUMPTIONS" if assumptions else "READY")
    json.dump({"period_end": f"{pe[0]}-{pe[1]:02d}", "period_end_source": pe_src, "ebitda_route": route,
               "bridge_route": bridge, "concepts": out, "questions": questions, "assumptions_ranked": assumptions,
               "assumptions": assumptions,
               "layout_checks": idx.get("layout_checks", []), "status": status},
              open(a.out, "w", encoding="utf-8"), indent=1, default=str)
    print(f"MAPPING STATUS: {status} | period end {pe[0]}-{pe[1]:02d} ({pe_src}) | EBITDA route: "
          f"{' + '.join(route) if route else 'NONE'} | bridge: {bridge or 'NONE'}")
    for cid, m in out.items():
        if m["status"] == "mapped":
            ls = m["lines"]
            print(f"- {cid}: {m['match']} -> " + "; ".join(f"'{l['label']}' ({l['file']} / {l['sheet']}, {l['frequency']}, "
                                                             f"{l['periods'][0]}..{l['periods'][-1]})" for l in ls))
        else:
            print(f"- {cid}: {m['status']}" + (f" ({m.get('reason')})" if m.get("reason") else ""))
    if out.get("debt", {}).get("match") == "sum_of_components" and bridge == "debt_less_cash":
        print("FLAG: debt is the SUM of these lines: " + ", ".join(f"'{l['label']}'" for l in out["debt"]["lines"])
              + " - list this in the final summary for the analyst to confirm")
    W = [("multiple not given", 3.0), ("units not given", 1.5), ("several lines match", 1.8), ("ownership not given", 1.5),
         ("period end not given", 1.2), ("discount not given", 1.0), ("claims", 0.8), ("adjustments not given", 0.8)]
    def weight(x):
        return next((w for k, w in W if k in x.lower()), 1.0)
    if out.get("debt", {}).get("match") == "sum_of_components" and bridge == "debt_less_cash":
        assumptions.append("Debt is the sum of several lines: " + ", ".join(f"'{l['label']}'" for l in out["debt"]["lines"]) + ". Confirm the lines.")
    assumptions = [x for _, x in sorted(((weight(x), x) for x in assumptions), key=lambda t: -t[0])]
    assumptions += [f"statement pack: {x}" for x in idx.get("layout_checks", [])]
    for q in questions:
        print(f"BLOCKER: {q}")
    for x in assumptions:
        print(f"ASSUMPTION: {x}")
    print(f"FILE WRITTEN: {a.out}")
    print("NEXT REQUIRED STEP: " + ("do not ask the user now: report every BLOCKER and ASSUMPTION in the final summary "
                                    "and stop." if questions else "run build_workbook.py. Do not ask the user anything; "
                                    "every ASSUMPTION goes in the final summary."))
    return 3 if questions else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources-index", required=True); ap.add_argument("--answers"); ap.add_argument("--out", required=True)
    try:
        sys.exit(main(ap.parse_args()))
    except Exception as e:
        print(f"MAPPING_ERROR: {type(e).__name__}: {e}"); sys.exit(1)
