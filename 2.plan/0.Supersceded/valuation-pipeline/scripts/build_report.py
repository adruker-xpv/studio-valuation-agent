# build_report.py - writes the end-of-run report deterministically from the files (no LLM prose)
# Usage: python build_report.py <stem>_inputs_skeleton.json <stem>_input_map.json --out <stem>_run_report.md
import sys, os, argparse
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_input_map import evaluate


def row(i, e, tag=""):
    return (f"| {i}{tag} | {e['label']} | {', '.join(e['sample_values'][:4])} | {e['type']} / "
            f"{e.get('confidence')} | {(e.get('notes') or '').replace('|', '/')} |")


def main(skel_path, map_path, out):
    r = evaluate(skel_path, map_path)
    skel = r["skel"]
    L = [f"# Run report: {skel['workbook']}", ""]
    if r["status"] == "INVALID":
        L += ["**Technical status: INVALID** (input map failed validation)", r.get("recon", ""), "",
              "## Input map problems"] + [f"- {x}" for x in r["errors"][:50]]
        open(out, "w", encoding="utf-8").write("\n".join(L))
        print(f"REPORT WRITTEN: {out}\nSTATUS: INVALID")
        return
    ents = r["entries"]
    n_open = len(r["unresolved"]) + len(r["low_conf"]) + len(r["medium_conf"])
    L += [f"**Technical status: {r['status']}** | **Business review: {r['business']}** "
          f"({len(r['reviewed'])}/{len(r['material'])} material blocks confirmed by an analyst)  ",
          r["recon"], "",
          "_Technical status = structurally complete and machine checks pass. It does not mean the business "
          "classifications are correct; that requires business review CONFIRMED._", "",
          "## Technical gates"] + [f"- {'PASS' if ok else 'FAIL'}: {g}" for g, ok in r["gates"].items()]
    L += ["", "## Controls (from Excel's last saved values)", "| Cell | Result | Value | Expected | Severity |",
          "|---|---|---|---|---|"]
    L += [f"| {c['cell']} | {c['result']} | {c['value']} | {c['expected']}"
          f"{' +/- ' + str(c['absolute_tolerance']) if c['control_type'] == 'numeric' else ''} | {c['severity']} |"
          for c in r["controls"]] or ["| (no controls defined) | | | | |"]
    L += ["", "## Key outputs chosen (proposed)", "| Cell | Reason |", "|---|---|"]
    L += [f"| {c} | {skel.get('key_output_reasons', {}).get(c, '')} |" for c in skel["key_outputs"]] or ["| (none) | |"]
    L += ["", "## Classifications (proposed)", "| Type | Blocks | high | medium | low |", "|---|---|---|---|---|"]
    for t, n in r["counts"].items():
        if n and t != "not_material":
            cs = [e.get("confidence") for e in ents.values() if e["type"] == t]
            L.append(f"| {t} | {n} | {cs.count('high')} | {cs.count('medium')} | {cs.count('low')} |")
    kos = len(skel.get("key_outputs") or []) or 1
    rv = []
    def item(impact, unc, what, why):
        rv.append((round(impact * unc, 2), what, why))
    for c in r["controls"]:
        if c["result"] != "PASS":
            item(3, 1.0 if c["severity"] == "blocking" else 0.6, c["cell"], f"control {c['result']}: value {c['value']}, expected {c['expected']}")
    for b in r["blocking"]:
        item(3, 1.0, "blocking issue", b)
    for tag, lst, unc in (("UNRESOLVED", r["unresolved"], 1.0), ("low confidence", r["low_conf"], 0.7), ("medium confidence", r["medium_conf"], 0.4)):
        for i in lst:
            e = ents[i]
            imp = 2 + min(1.0, len(e.get("feeds_key_outputs") or []) / kos)
            item(imp, unc, f"{i} ({e['label']})", f"{tag}: {e['type']}; {(e.get('notes') or '')[:140]}")
    sc_open = {}
    for i in r.get("scope_open", []):
        sc_open[ents[i]["sheet"]] = sc_open.get(ents[i]["sheet"], 0) + 1
    for sh, n in sc_open.items():
        item(1, 0.5, f"reporting scope: {sh}", f"{n} blocks not feeding a key output; confirm whether they need a quarterly refresh")
    if r["cadence_unconfirmed"]:
        item(2, 0.2, "refresh cadence", f"{len(r['cadence_unconfirmed'])} material blocks have a proposed, unconfirmed cadence")
    hc = sum(1 for i in r["material"] if ents[i].get("confidence") == "high" and not ents[i].get("reviewed_by"))
    if hc:
        item(2, 0.1, "high-confidence classifications", f"{hc} blocks awaiting a bulk confirmation")
    rv.sort(key=lambda x: -x[0])
    L += ["", "## Review list (highest priority first: impact x uncertainty)", "| # | Priority | Item | Why |", "|---|---|---|---|"]
    L += [f"| {k} | {x[0]:.2f} | {x[1]} | {x[2].replace('|', '/')} |" for k, x in enumerate(rv, 1)] or ["| - | - | nothing to review | |"]
    L += ["", f"## Needs analyst input ({n_open} items, plus cadence and scope below)",
          "| Input | Label | Current values | Type / confidence | Agent note |", "|---|---|---|---|---|"]
    for i in r["unresolved"]:
        L.append(row(i, ents[i], " (UNRESOLVED)"))
    for i in r["low_conf"]:
        L.append(row(i, ents[i], " (low)"))
    for i in r["medium_conf"]:
        L.append(row(i, ents[i], " (medium)"))
    if not n_open:
        L.append("| (no unresolved, low or medium items) | | | | |")
    L += ["", f"**Refresh cadence to confirm:** {len(r['cadence_unconfirmed'])} material blocks have a proposed "
          "cadence that no analyst has confirmed. A single workbook cannot evidence cadence.",
          f"**High-confidence blocks awaiting confirmation:** "
          f"{sum(1 for i in r['material'] if ents[i].get('confidence') == 'high' and not ents[i].get('reviewed_by'))}"]
    tab = {}
    for i in r["auto_not_material"]:
        e = ents[i]
        t = tab.setdefault(e["sheet"], Counter())
        t[e.get("reporting_required")] += 1
        t["cells"] += e["n_cells"]
    L += ["", f"## Reporting scope: {len(r['auto_not_material'])} blocks do not feed a key output",
          "Not valuation-material, but they may still need quarterly refresh for LP reporting, disclosure or supporting "
          "schedules. Mark each sheet reporting-required yes or no.",
          "| Sheet | Blocks | Cells | yes | no | unconfirmed |", "|---|---|---|---|---|---|"]
    L += [f"| {sh} | {t['yes'] + t['no'] + t['unconfirmed']} | {t['cells']} | {t['yes']} | {t['no']} | {t['unconfirmed']} |"
          for sh, t in sorted(tab.items(), key=lambda x: -x[1]["cells"])] or ["| (none) | | | | | |"]
    L += ["", "## Blocking issues"] + ([f"- {b}" for b in r["blocking"]] or ["- (none)"])
    bn = r["broken_names"]
    if bn:
        used = [n for n in bn if n.get("used_by_formulas")]
        L += ["", f"## Broken or external named ranges: {len(bn)} ({len(used)} used by formulas)",
              "Listed in full in the schema file. Impact on future updates is not assessed."]
        if used:
            L.append("Used by formulas: " + ", ".join(n["name"] for n in used[:10]) + (" ..." if len(used) > 10 else ""))
    L += ["", "## How to correct or confirm",
          "- Corrections: `Inputs!B6: assumption, changes each quarter: yes, note: management adjustment factor`",
          "- Confirmations: `Confirm all financial_statement blocks - reviewed by <name>` or "
          "`Confirm Quarterly!B2:E2, Valuation!B3 - reviewed by <name>`",
          "- Reporting scope: `Reporting scope: LP Report yes, Comp Detail no - reviewed by <name>`",
          "- Controls: `Control 'Valuation Summary'!F44: boolean, expected TRUE, blocking`",
          "- Valuation scope: `Key outputs: add 'LP Report'!D49:D51` makes more inputs valuation-material."]
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print(f"REPORT WRITTEN: {out}")
    print(f"technical status: {r['status']} | business review: {r['business']} | analyst items: {n_open}")
    failing = [c for c in r["controls"] if c["result"] != "PASS"]
    ctrl_line = ("Controls: none defined in key_outputs.json." if not r["controls"] else
                 "Controls: all " + str(len(r["controls"])) + " pass." if not failing else
                 "Controls failing: " + "; ".join(f"{c['cell']} = {c['value']} (expected {c['expected']}, {c['severity']})" for c in failing))
    print(f"CONTROLS LINE: {ctrl_line}")
    print("GATES LINE: " + "; ".join(f"{g} {'PASS' if ok else 'FAIL'}" for g, ok in r["gates"].items()))
    print("NEXT REQUIRED STEP (J3/P5): save the files, then give the final summary. Its first line must be exactly: "
          f"'Structure initialization: technical status {r['status']}; business review {r['business']}.' "
          "Then the CONTROLS LINE and GATES LINE exactly as printed (gates are not controls). "
          "Then the report's 'Review list' unchanged and in its order (it replaces the Needs analyst input table in the summary). Never write 'none' for analyst input unless "
          "the report says so and business review is CONFIRMED. If source statements were uploaded, run "
          "valuation-mapping-profile before the final summary.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("skeleton"); ap.add_argument("input_map"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    main(a.skeleton, a.input_map, a.out)
